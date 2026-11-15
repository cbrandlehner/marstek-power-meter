# Marstek Power Meter

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-integration-41BDF5?logo=home-assistant&logoColor=white)](https://www.home-assistant.io/)
[![License: MPL-2.0](https://img.shields.io/badge/License-MPL--2.0-brightgreen.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.1-blue.svg)](https://github.com/cbrandlehner/marstek-power-meter)
[![GitHub stars](https://img.shields.io/github/stars/cbrandlehner/marstek-power-meter?style=social&label=Star%20on%20GitHub)](https://github.com/cbrandlehner/marstek-power-meter)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/cbrandlehner?label=Sponsor)](https://github.com/sponsors/cbrandlehner)
[![Unofficial](https://img.shields.io/badge/vendor_support-none-lightgrey.svg)](#hinweis)

Home-Assistant-Integration für das Marstek CT002 (`HME-4` und neueres `TPM2-0`) und das CT003 (`HME-3`). Sie liest Netzleistung und WLAN-Empfang per UDP vom Zähler. Die Abfrage nutzt eine eigene Poller-MAC, Phase 0, Leistung 0 und `participate=0`, damit sie nicht in die Aggregation der Akkus eingeht.

| | |
|---|---|
| Domain | `marstek_power_meter` |
| Name in Home Assistant | Marstek Power Meter |
| Version | 1.0.1 |
| Abfrage | UDP-Port 12345, alle 5 Sekunden, bis zu 3 Versuche je Abfrage |
| Lizenz | [MPL-2.0](LICENSE) |

## Hinweis

Marstek Power Meter ist ein unabhängiges Open-Source-Projekt ohne Herstellersupport. Es steht in keiner Verbindung zu Marstek und wird von Marstek nicht unterstützt. Der Betrieb erfolgt auf eigene Gefahr.

## Installation

### HACS

1. HACS öffnen, dann **Integrationen** und **Benutzerdefinierte Repositories**.
2. `https://github.com/cbrandlehner/marstek-power-meter` eintragen, Kategorie **Integration**.
3. **Marstek Power Meter** installieren und Home Assistant neu starten.
4. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach **Marstek Power Meter** suchen.

Ab Home Assistant 2026.11 liegt HACS im Marketplace. Ein benutzerdefiniertes Repository wird dort genauso hinzugefügt.

### Manuell

Den Ordner `custom_components/marstek_power_meter` nach `<config>/custom_components/marstek_power_meter` kopieren und Home Assistant neu starten. Danach die Integration wie oben hinzufügen.

## Einrichtung

Die MAC-Adresse des CT-Zählers steht in der Marstek-App unter Geräteverwaltung. Es sind 12 Hex-Zeichen, mit oder ohne Doppelpunkte. `000000000000` ist ebenfalls gültig. Die Integration übernimmt danach die MAC aus der Antwort.

Die Poller-MAC ist eine eigene Kennung dieser Integration. Die Vorgabe ist eine lokal vergebene Adresse. Sie darf nicht die MAC eines Akkus sein, weil der Zähler pro MAC einen Slot führt.

| Feld | Bedeutung |
|---|---|
| IP-Adresse | Adresse des CT-Zählers im LAN |
| Poller-MAC | Eigene Kennung dieser Abfrage, nicht die MAC eines Akkus |
| MAC-Adresse des CT-Zählers | Zähler selbst, aus der Marstek-App |
| Speicher-Typ | `HMG` Venus, `HMB` B2500 v1, `HMA` B2500 v2, `HMK` Greensolar v3 |
| Speicher-Nummer | Typnummer, Vorgabe `50` (ergibt zum Beispiel `HMG-50`) |
| CT-Typ | `HME-4` für das CT002, `TPM2-0` für ein neueres CT002, `HME-3` für das CT003 |

Direkt nach dem Hinzufügen sichtbar sind Gesamtleistung, die drei Phasen und der WLAN-RSSI. Tarif-Energiezähler gibt es nur bei CT003 und neuerem CT002 (`TPM2-0`). Ein originales CT002 (`HME-4`) sendet sie nicht.

## Herkunft

Marstek Power Meter ist ein eigenständiges Projekt. Es beruht auf [hass_marstek-smart-meter](https://github.com/d-shmt/hass_marstek-smart-meter). Der Autor des Originals pflegt das Repository nicht mehr und hat auf Pull Requests nicht reagiert. Deshalb wurde dieses Projekt neu angelegt.

## Lizenz

Dieses Programm steht unter der [Mozilla Public License 2.0](LICENSE). Der vollständige Text liegt in `LICENSE`. Jede Quelldatei unter `custom_components/marstek_power_meter/` trägt diesen Hinweis:

> This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

## Unterstützung

- [Repository auf GitHub markieren](https://github.com/cbrandlehner/marstek-power-meter)
- [Fehler und Fragen im Issue-Tracker](https://github.com/cbrandlehner/marstek-power-meter/issues)
- [Maintainer über GitHub Sponsors unterstützen](https://github.com/sponsors/cbrandlehner)
