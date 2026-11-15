# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Parser and payload tests. They do not talk to a meter."""
import sys
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


if __name__ == "__main__":
    unittest.main()
