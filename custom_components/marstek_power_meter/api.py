# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""API for the Marstek Power Meter integration."""
from __future__ import annotations

import logging
import re
import socket
import time

_LOGGER = logging.getLogger(__name__)

SOH = 0x01
STX = 0x02
ETX = 0x03

# Identity fields are copied through as text. A numeric MAC must not become an int.
STRING_LABELS = frozenset(
    {
        "meter_dev_type",
        "meter_mac_code",
        "hhm_dev_type",
        "hhm_mac_code",
    }
)

RESPONSE_LABELS = (
    "meter_dev_type",
    "meter_mac_code",
    "hhm_dev_type",
    "hhm_mac_code",
    "A_phase_power",
    "B_phase_power",
    "C_phase_power",
    "total_power",
    "A_chrg_nb",
    "B_chrg_nb",
    "C_chrg_nb",
    "ABC_chrg_nb",
    "wifi_rssi",
    "info_idx",
    "x_chrg_power",
    "A_chrg_power",
    "B_chrg_power",
    "C_chrg_power",
    "ABC_chrg_power",
    "x_dchrg_power",
    "A_dchrg_power",
    "B_dchrg_power",
    "C_dchrg_power",
    "ABC_dchrg_power",
)

# CT003 and newer CT002 (TPM2-0) append these. Original HME-4 does not.
# Each count is 0.1 Wh.
ENERGY_LABELS = (
    "low_price_ele_in",
    "normal_price_ele_in",
    "low_price_ele_out",
    "normal_price_ele_out",
)
ENERGY_WH_PER_COUNT = 0.1

_MAC_RE = re.compile(r"[0-9A-Fa-f]{12}")


def canonical_mac(value: str) -> str:
    """Return a 12-digit hex MAC without separators.

    The CT MAC field is only 13 characters wide, so colon form is rejected.
    """
    compact = re.sub(r"[:\-\s.]", "", value.strip())
    if _MAC_RE.fullmatch(compact) is None:
        raise ValueError("MAC must be 12 hex digits")
    # The CT compares the MAC byte for byte, including case.
    return compact


class MarstekCtApi:
    """API to communicate with the Marstek CT meter."""

    def __init__(self, host, device_type, battery_mac, ct_mac, ct_type):
        self._host = host
        self._port = 12345
        self._device_type = device_type
        self._battery_mac = battery_mac
        self._ct_mac = ct_mac
        self._ct_type = ct_type

        # One lost UDP packet would otherwise mark every sensor unavailable.
        self._timeout = 3.0
        self._retries = 3
        self._retry_delay = 0.3

        self._payload = self._build_payload()

    def _build_payload(self) -> bytes:
        """Build an inspection poll that does not join battery aggregation.

        Phase 0 and 0 W leave the CT aggregates unchanged. participate=0 is
        explicit on firmware that reads the seventh field; older firmware
        ignores it and still sees phase 0 / 0 W.
        """
        separator = "|"
        message_fields = [
            self._device_type,
            self._battery_mac,
            self._ct_type,
            self._ct_mac,
            "0",
            "0",
            "0",
        ]
        message_bytes = (separator + separator.join(message_fields)).encode("ascii")

        base_size_without_len = 1 + 1 + len(message_bytes) + 1 + 2
        length_str = str(base_size_without_len + len(str(base_size_without_len)))
        while True:
            total_length = base_size_without_len + len(length_str)
            new_length_str = str(total_length)
            if new_length_str == length_str:
                break
            length_str = new_length_str

        payload = bytearray([SOH, STX])
        payload.extend(length_str.encode("ascii"))
        payload.extend(message_bytes)
        payload.append(ETX)

        xor_val = 0
        for byte in payload:
            xor_val ^= byte
        payload.extend(f"{xor_val:02x}".encode("ascii"))
        return bytes(payload)

    def _extract_message_ascii(self, data: bytes) -> str:
        """Extract the ascii message between the first '|' and ETX."""
        try:
            etx_pos = data.index(bytes([ETX]))
        except ValueError as exc:
            raise ValueError("ETX not found in response") from exc

        frame = data[:etx_pos]
        try:
            pipe_pos = frame.index(b"|")
        except ValueError as exc:
            raise ValueError("No '|' separator found in response") from exc

        return frame[pipe_pos:].decode("ascii")

    def _decode_response(self, data: bytes) -> dict:
        """Parse the UDP response."""
        try:
            message = self._extract_message_ascii(data)
        except (UnicodeDecodeError, ValueError) as err:
            return {"error": f"Invalid response format: {err}"}

        fields = message.split("|")[1:]
        parsed: dict[str, object] = {}
        for label, val in zip(RESPONSE_LABELS, fields):
            parsed[label] = self._parse_field(label, val)

        for label in RESPONSE_LABELS[len(fields) :]:
            parsed[label] = None

        extra = fields[len(RESPONSE_LABELS) :]
        while extra and extra[-1] == "":
            extra = extra[:-1]
        for label, val in zip(ENERGY_LABELS, extra):
            parsed[label] = self._parse_energy(val)

        return parsed

    @staticmethod
    def _parse_field(label: str, val: str) -> object:
        if val == "":
            return None
        if label in STRING_LABELS:
            return val
        try:
            return int(val)
        except ValueError:
            return val

    @staticmethod
    def _parse_energy(val: str) -> float | None:
        if val == "":
            return None
        try:
            return int(val) * ENERGY_WH_PER_COUNT
        except ValueError:
            return None

    def _exchange(self) -> bytes:
        """Send one datagram and wait for its reply."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(self._timeout)
            sock.sendto(self._payload, (self._host, self._port))
            response, _ = sock.recvfrom(2048)
            return response

    def fetch_data(self) -> dict:
        """Blocking poll. The caller awaits the whole retry loop."""
        last_error = "No response from meter"
        for attempt in range(1, self._retries + 1):
            try:
                return self._decode_response(self._exchange())
            except socket.timeout:
                last_error = "Timeout - No response from meter"
                _LOGGER.debug(
                    "Marstek CT timeout (attempt %d/%d, timeout=%.1fs)",
                    attempt,
                    self._retries,
                    self._timeout,
                )
            except Exception as err:
                last_error = f"Unexpected error: {err}"
                _LOGGER.warning(
                    "Marstek CT unexpected error on attempt %d/%d: %s",
                    attempt,
                    self._retries,
                    err,
                )
            if attempt < self._retries:
                time.sleep(self._retry_delay)
        return {"error": last_error}


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""
