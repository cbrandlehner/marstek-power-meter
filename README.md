# Marstek Power Meter

[![HACS](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://www.home-assistant.io/integrations/marketplace/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-integration-41BDF5?logo=home-assistant&logoColor=white)](https://www.home-assistant.io/)
[![License: MPL-2.0](https://img.shields.io/badge/License-MPL--2.0-brightgreen.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/cbrandlehner/marstek-power-meter)
[![GitHub stars](https://img.shields.io/github/stars/cbrandlehner/marstek-power-meter?style=social&label=Star%20on%20GitHub)](https://github.com/cbrandlehner/marstek-power-meter)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/cbrandlehner?label=Sponsor)](https://github.com/sponsors/cbrandlehner)
[![Unofficial](https://img.shields.io/badge/vendor_support-none-lightgrey.svg)](#notice)

Home Assistant integration for the Marstek CT002 (`HME-4` and the newer `TPM2-0`) and the CT003 (`HME-3`). It reads grid power and Wi-Fi signal strength from the meter over UDP. Each poll uses its own poller MAC, phase 0, 0 W, and `participate=0`, so the poll stays out of the battery aggregation.

| | |
|---|---|
| Domain | `marstek_power_meter` |
| Name in Home Assistant | Marstek Power Meter |
| Version | 1.1.0 |
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

Add the integration and enter the IP address of the CT meter. Nothing else is required.

Setup sends an inspection poll to UDP port 12345: phase 0, 0 W, and `participate=0`. The poll carries a generated poller MAC, the label `HMG-50`, and the wildcard CT MAC `000000000000`. The meter answers that wildcard, and it answers only its own CT type. Setup tries `TPM2-0`, then `HME-4`, then `HME-3`. Each try waits up to 1 second and is sent a second time when the first packet gets no reply. The first answer is kept. Its CT type and CT MAC are stored.

| Stored value | Source |
|---|---|
| IP address | The address entered in the form |
| Poller MAC | Generated for this integration. It is not a battery MAC. |
| CT MAC | Taken from the reply |
| Storage | `HMG-50`. The meter does not check this label. |
| CT type | `TPM2-0` for a newer CT002, `HME-4` for an original CT002, `HME-3` for the CT003 |

Total power, the three phases, and Wi-Fi RSSI appear after setup. Tariff energy counters appear when the reply includes them. The CT003 and the newer CT002 (`TPM2-0`) send them. An original CT002 (`HME-4`) does not. An entry created before 1.1.0 keeps the values it already stored. Delete that entry and add the integration again to detect them.

When the meter does not answer, use [Troubleshooting](#troubleshooting).

## Troubleshooting

After setup, each poll sends one UDP datagram to port 12345 and waits up to 3 seconds for the reply, with two further attempts. The datagram is the same inspection poll as setup. It stays out of the battery aggregation. The command-line probes below try the three CT types the same way setup does.

### Reachability and Docker

The meter listens on UDP port 12345. Home Assistant sends to that port, and the reply has to come back to Home Assistant.

- Keep the meter and Home Assistant on a LAN path that forwards UDP. Guest networks and Wi-Fi client isolation drop these packets.
- On a firewall or between VLANs, allow UDP from Home Assistant to the meter address, destination port 12345, and allow the reply back to Home Assistant.
- When the host firewall limits outgoing traffic, open that path. With `ufw`, replace the address with the meter IP:

```bash
sudo ufw allow out proto udp to 192.168.1.50 port 12345
```

On Linux, run the Home Assistant container on the host network so it uses the host route to the meter:

```yaml
network_mode: host
```

Leave UDP port 12345 unpublished. With host networking, the host firewall rule above is the one that applies.

On Docker Desktop for macOS and Windows, host networking stays inside the Docker virtual machine. Run the probe on the host, then run it again inside the container. A reply on the host and silence in the container means the container has no route to the meter. Run Home Assistant in a bridged virtual machine, or use Home Assistant OS, on the same LAN as the meter.

Home Assistant OS already attaches the system to the LAN. A router rule between VLANs still has to allow UDP port 12345 to the meter.

### CT types

| Meter | CT type the meter answers | Tariff energy counters |
|---|---|---|
| CT002, newer | `TPM2-0` | yes |
| CT002, original | `HME-4` | no |
| CT003 | `HME-3` | yes |

The meter compares the CT type and the CT MAC byte for byte, including letter case. A request whose CT type is any other value gets no reply. `000000000000` is the wildcard CT MAC. The reply carries the meter's own type and MAC in the first two fields.

### Command-line probe

Change the IP address, then run the probe on a computer on the same LAN as the meter. It tries `TPM2-0`, `HME-4`, and `HME-3` with the wildcard CT MAC. The printed type and the following line mean the meter answered. Fields on that line are separated by `|`. The first two are the meter type and the meter MAC. The next two echo `HMG-50` and the poller MAC. The next four numbers are phase A, phase B, phase C, and total power in watts.

`No reply from the meter` means none of the three datagrams came back. Check the IP, the LAN path, and the firewall or Docker route.

Linux and macOS:

```bash
python3 - << 'PY'
import socket
import sys

ip = "192.168.1.50"

def probe(ct_type):
    message = f"|HMG-50|02A57E00C2A1|{ct_type}|000000000000|0|0|0".encode("ascii")
    base = 5 + len(message)
    length = str(base + len(str(base)))
    while str(base + len(length)) != length:
        length = str(base + len(length))
    payload = bytearray([0x01, 0x02])
    payload += length.encode("ascii") + message + bytes([0x03])
    checksum = 0
    for byte in payload:
        checksum ^= byte
    payload += f"{checksum:02x}".encode("ascii")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1)
    sock.sendto(bytes(payload), (ip, 12345))
    try:
        data, _ = sock.recvfrom(2048)
    except socket.timeout:
        return None
    text = data.split(bytes([0x03]), 1)[0]
    return text.split(b"|", 1)[1].decode("ascii")

for ct_type in ("TPM2-0", "HME-4", "HME-3"):
    reply = probe(ct_type)
    if reply:
        print(ct_type)
        print(reply)
        break
else:
    sys.exit("No reply from the meter")
PY
```

To run that probe inside the Home Assistant container, use the container's Python and the same script. Replace `homeassistant` with the name from `docker ps` when it differs:

```bash
docker exec -i homeassistant python3 - << 'PY'
import socket
import sys

ip = "192.168.1.50"

def probe(ct_type):
    message = f"|HMG-50|02A57E00C2A1|{ct_type}|000000000000|0|0|0".encode("ascii")
    base = 5 + len(message)
    length = str(base + len(str(base)))
    while str(base + len(length)) != length:
        length = str(base + len(length))
    payload = bytearray([0x01, 0x02])
    payload += length.encode("ascii") + message + bytes([0x03])
    checksum = 0
    for byte in payload:
        checksum ^= byte
    payload += f"{checksum:02x}".encode("ascii")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1)
    sock.sendto(bytes(payload), (ip, 12345))
    try:
        data, _ = sock.recvfrom(2048)
    except socket.timeout:
        return None
    text = data.split(bytes([0x03]), 1)[0]
    return text.split(b"|", 1)[1].decode("ascii")

for ct_type in ("TPM2-0", "HME-4", "HME-3"):
    reply = probe(ct_type)
    if reply:
        print(ct_type)
        print(reply)
        break
else:
    sys.exit("No reply from the meter")
PY
```

Windows PowerShell:

```powershell
$ip = "192.168.1.50"

function Send-MarstekProbe($ctType) {
    $msgBytes = [Text.Encoding]::ASCII.GetBytes("|HMG-50|02A57E00C2A1|$ctType|000000000000|0|0|0")
    $base = 5 + $msgBytes.Length
    $length = [string]($base + "$base".Length)
    while ([string]($base + $length.Length) -ne $length) {
        $length = [string]($base + $length.Length)
    }
    $payload = New-Object System.Collections.Generic.List[byte]
    $payload.Add(1)
    $payload.Add(2)
    $payload.AddRange([Text.Encoding]::ASCII.GetBytes($length))
    $payload.AddRange($msgBytes)
    $payload.Add(3)
    $checksum = 0
    foreach ($byte in $payload) { $checksum = $checksum -bxor $byte }
    $payload.AddRange([Text.Encoding]::ASCII.GetBytes("{0:x2}" -f $checksum))
    $udp = New-Object System.Net.Sockets.UdpClient
    $udp.Client.ReceiveTimeout = 1000
    $remote = New-Object System.Net.IPEndPoint ([Net.IPAddress]::Any, 0)
    try {
        [void]$udp.Send($payload.ToArray(), $payload.Count, $ip, 12345)
        $data = $udp.Receive([ref]$remote)
        $text = [Text.Encoding]::ASCII.GetString($data)
        $head = $text.Substring(0, $text.LastIndexOf([char]3))
        return $head.Substring($head.IndexOf("|") + 1)
    } catch {
        return $null
    } finally {
        $udp.Close()
    }
}

$answered = $false
foreach ($ctType in @("TPM2-0", "HME-4", "HME-3")) {
    $reply = Send-MarstekProbe $ctType
    if ($reply) {
        $ctType
        $reply
        $answered = $true
        break
    }
}
if (-not $answered) { "No reply from the meter" }
```

## Origin

Marstek Power Meter is a standalone project. It is based on [hass_marstek-smart-meter](https://github.com/d-shmt/hass_marstek-smart-meter). The author of the original no longer maintains the repository and did not respond to pull requests, so this project was created.

## License

This program is licensed under the [Mozilla Public License 2.0](LICENSE). The full text is in `LICENSE`. Each source file under `custom_components/marstek_power_meter/` carries this notice:

> This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

## Support

- [Star this repository on GitHub](https://github.com/cbrandlehner/marstek-power-meter)
- [Report bugs and questions in the issue tracker](https://github.com/cbrandlehner/marstek-power-meter/issues)
- [Sponsor the maintainer on GitHub Sponsors](https://github.com/sponsors/cbrandlehner)
