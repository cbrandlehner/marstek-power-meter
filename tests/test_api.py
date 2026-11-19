# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Parser, payload, and discovery tests. Discovery talks to a local UDP fake."""
import socket
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "custom_components" / "marstek_power_meter"),
)

from api import (  # noqa: E402
    ETX,
    SOH,
    STX,
    MarstekCtApi,
    canonical_mac,
    discover_meter,
)


def frame(body: str) -> bytes:
    message = body.encode("ascii")
    base = 1 + 1 + len(message) + 1 + 2
    length = str(base + len(str(base)))
    while str(base + len(length)) != length:
        length = str(base + len(length))
    payload = bytearray([SOH, STX])
    payload.extend(length.encode("ascii"))
    payload.extend(message)
    payload.append(ETX)
    xor_val = 0
    for byte in payload:
        xor_val ^= byte
    payload.extend(f"{xor_val:02x}".encode("ascii"))
    return bytes(payload)


class ApiTests(unittest.TestCase):
    def test_canonical_mac_strips_separators(self):
        self.assertEqual(canonical_mac("aa:bb:cc:dd:ee:ff"), "aabbccddeeff")
        self.assertEqual(canonical_mac("001122334455"), "001122334455")
        with self.assertRaises(ValueError):
            canonical_mac("not-a-mac")

    def test_payload_is_inspection_poll(self):
        api = MarstekCtApi(
            "127.0.0.1",
            "HMG-50",
            "02A57E00C2A1",
            "001122334455",
            "HME-4",
        )
        text = api._payload.decode("ascii")
        self.assertIn("|HMG-50|02A57E00C2A1|HME-4|001122334455|0|0|0", text)
        self.assertNotIn(":", text)

    def test_digit_mac_stays_text_and_grid_is_not_copied_into_buckets(self):
        api = MarstekCtApi("127.0.0.1", "HMG-50", "02A57E00C2A1", "001122334455", "HME-4")
        body = (
            "|HME-4|001122334455|HMG-50|02A57E00C2A1"
            "|5|-34|28|0|0|0|0|0|-80|7|0|0|0|0|0|0|0|0|0|0|"
        )
        parsed = api._decode_response(frame(body))
        self.assertEqual(parsed["meter_mac_code"], "001122334455")
        self.assertIsInstance(parsed["meter_mac_code"], str)
        self.assertEqual(parsed["A_phase_power"], 5)
        self.assertEqual(parsed["ABC_chrg_power"], 0)
        self.assertEqual(parsed["ABC_dchrg_power"], 0)
        self.assertNotIn("low_price_ele_in", parsed)

    def test_energy_fields_scale_to_watt_hours(self):
        api = MarstekCtApi("127.0.0.1", "HMG-50", "02A57E00C2A1", "001122334455", "HME-3")
        body = (
            "|HME-3|001122334455|HMG-50|02A57E00C2A1"
            "|1|2|3|6|0|0|0|0|-70|1|0|0|0|0|0|0|0|0|0|0|"
            "100|0|20|0"
        )
        parsed = api._decode_response(frame(body))
        self.assertEqual(parsed["low_price_ele_in"], 10.0)
        self.assertEqual(parsed["normal_price_ele_in"], 0.0)
        self.assertEqual(parsed["low_price_ele_out"], 2.0)
        self.assertEqual(parsed["normal_price_ele_out"], 0.0)
        self.assertEqual(parsed["A_chrg_nb"], 0)


class FakeMeter:
    """UDP peer that answers one CT type and only an inspection poll."""

    def __init__(self, ct_type: str, ct_mac: str, tail: str) -> None:
        self.ct_type = ct_type
        self.ct_mac = ct_mac
        self.tail = tail
        self.seen: list[list[str]] = []
        self._stop = threading.Event()
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind(("127.0.0.1", 0))
        self.port = self._sock.getsockname()[1]
        self._sock.settimeout(0.1)
        self._thread = threading.Thread(target=self._run, daemon=True)

    def __enter__(self) -> "FakeMeter":
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        self._thread.join(timeout=1)
        self._sock.close()

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                data, addr = self._sock.recvfrom(2048)
            except socket.timeout:
                continue
            try:
                etx = data.index(bytes([ETX]))
            except ValueError:
                continue
            fields = [part.decode("ascii") for part in data[:etx].split(b"|")[1:]]
            self.seen.append(fields)
            if len(fields) < 7:
                continue
            device, poller, ct_type, ct_mac, phase, power, participate = fields[:7]
            if ct_type != self.ct_type or ct_mac != "000000000000":
                continue
            if (phase, power, participate) != ("0", "0", "0"):
                continue
            body = f"|{self.ct_type}|{self.ct_mac}|{device}|{poller}|{self.tail}"
            self._sock.sendto(frame(body), addr)


POWER_TAIL = "5|-34|28|0|0|0|0|0|-80|7|0|0|0|0|0|0|0|0|0|0|"
ENERGY_TAIL = "1|2|3|6|0|0|0|0|-70|1|0|0|0|0|0|0|0|0|0|0|100|0|20|0"


class DiscoverTests(unittest.TestCase):
    def test_silent_type_does_not_hide_the_meter_that_answers(self):
        """Stored identity comes from the reply, and the probe stays an inspection poll."""
        with FakeMeter("HME-4", "AABBCCDDEEFF", POWER_TAIL) as meter:
            found = discover_meter(
                "127.0.0.1",
                "02A57E00C2A1",
                port=meter.port,
                timeout=0.4,
                retries=1,
            )
        self.assertEqual(
            found,
            {
                "host": "127.0.0.1",
                "device_type": "HMG-50",
                "battery_mac": "02A57E00C2A1",
                "ct_mac": "AABBCCDDEEFF",
                "ct_type": "HME-4",
            },
        )
        self.assertTrue(meter.seen)
        for fields in meter.seen:
            self.assertEqual(fields[0], "HMG-50")
            self.assertEqual(fields[1], "02A57E00C2A1")
            self.assertEqual(fields[3], "000000000000")
            self.assertEqual(fields[4:7], ["0", "0", "0"])

    def test_energy_counters_mark_the_meter(self):
        with FakeMeter("TPM2-0", "001122334455", ENERGY_TAIL) as meter:
            found = discover_meter(
                "127.0.0.1",
                "02A57E00C2A1",
                port=meter.port,
                timeout=0.4,
                retries=1,
            )
        self.assertEqual(found["ct_type"], "TPM2-0")
        self.assertEqual(found["ct_mac"], "001122334455")
        self.assertTrue(found["has_energy"])

    def test_no_reply_is_an_error(self):
        with FakeMeter("NOPE", "AABBCCDDEEFF", POWER_TAIL) as meter:
            found = discover_meter(
                "127.0.0.1",
                "02A57E00C2A1",
                port=meter.port,
                timeout=0.2,
                retries=1,
            )
        self.assertIn("error", found)
        self.assertNotIn("ct_mac", found)


if __name__ == "__main__":
    unittest.main()
