# Marstek Power Meter

[![HACS](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://www.home-assistant.io/integrations/marketplace/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-integration-41BDF5?logo=home-assistant&logoColor=white)](https://www.home-assistant.io/)
[![License: MPL-2.0](https://img.shields.io/badge/License-MPL--2.0-brightgreen.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.1-blue.svg)](https://github.com/cbrandlehner/marstek-power-meter)
[![GitHub stars](https://img.shields.io/github/stars/cbrandlehner/marstek-power-meter?style=social&label=Star%20on%20GitHub)](https://github.com/cbrandlehner/marstek-power-meter)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/cbrandlehner?label=Sponsor)](https://github.com/sponsors/cbrandlehner)
[![Unofficial](https://img.shields.io/badge/vendor_support-none-lightgrey.svg)](#notice)

Home Assistant integration for the Marstek CT002 (`HME-4` and the newer `TPM2-0`) and the CT003 (`HME-3`). It reads grid power and Wi-Fi signal strength from the meter over UDP. Each poll uses its own poller MAC, phase 0, 0 W, and `participate=0`, so the poll stays out of the battery aggregation.

| | |
|---|---|
| Domain | `marstek_power_meter` |
| Name in Home Assistant | Marstek Power Meter |
| Version | 1.0.1 |
| Polling | UDP port 12345, every 5 seconds, up to 3 attempts per poll |
| License | [MPL-2.0](LICENSE) |

## Notice

Marstek Power Meter is an independent open-source project with no vendor support. It is not affiliated with Marstek, and Marstek does not support it. Use it at your own risk.

## Installation

### Marketplace

On Home Assistant 2026.11 and newer, open **Settings → Marketplace** and search for **Marstek Power Meter**. Install it, then restart Home Assistant if it asks you to. Go to **Settings → Devices & services → Add integration** and search for **Marstek Power Meter**.

On Home Assistant 2026.10 and older, open HACS, then **Integrations**, and search for **Marstek Power Meter**. Install it, restart Home Assistant, then add the integration as above.

### Custom repository

Use this when search does not list it yet.

1. On Home Assistant 2026.11 and newer, open **Settings → Marketplace** and select **Add from link**. On older Home Assistant, open HACS, then **Integrations** and **Custom repositories**.
2. Add `https://github.com/cbrandlehner/marstek-power-meter` with category **Integration**.
3. Install **Marstek Power Meter** and restart Home Assistant.
4. Add the integration as described above.

### Manual

Copy the folder `custom_components/marstek_power_meter` to `<config>/custom_components/marstek_power_meter` and restart Home Assistant. Then add the integration as described above.

## Configuration

The CT MAC is on the Device Management page in the Marstek app. It is 12 hex characters, with or without colons. `000000000000` is also valid. The integration then stores the MAC from the reply.

The poller MAC is an identity of this integration. The suggested value is a locally assigned address. It must not be a battery MAC, because the meter keeps one slot per MAC.

| Field | Meaning |
|---|---|
| IP address | Address of the CT meter on the LAN |
| Poller MAC | Identity of this poll, not a battery MAC |
| CT MAC | The meter itself, from the Marstek app |
| Storage type | `HMG` Venus, `HMB` B2500 v1, `HMA` B2500 v2, `HMK` Greensolar v3 |
| Storage number | Type number, default `50` (for example `HMG-50`) |
| CT type | `HME-4` for the CT002, `TPM2-0` for a newer CT002, `HME-3` for the CT003 |

Total power, the three phases, and Wi-Fi RSSI are visible right after setup. Tariff energy counters exist only on the CT003 and the newer CT002 (`TPM2-0`). An original CT002 (`HME-4`) does not send them.

## Origin

Marstek Power Meter is a standalone project. It is based on [hass_marstek-smart-meter](https://github.com/d-shmt/hass_marstek-smart-meter). The author of the original no longer maintains the repository and did not respond to pull requests, so this project was created.

## License

This program is licensed under the [Mozilla Public License 2.0](LICENSE). The full text is in `LICENSE`. Each source file under `custom_components/marstek_power_meter/` carries this notice:

> This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

## Support

- [Star this repository on GitHub](https://github.com/cbrandlehner/marstek-power-meter)
- [Report bugs and questions in the issue tracker](https://github.com/cbrandlehner/marstek-power-meter/issues)
- [Sponsor the maintainer on GitHub Sponsors](https://github.com/sponsors/cbrandlehner)
