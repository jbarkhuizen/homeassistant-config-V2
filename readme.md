# Home Assistant Configuration V2

This repository contains my Home Assistant configuration files.

## System Information
- **Home Assistant Version**: Latest (Auto-updating)
- **Installation Type**: Home Assistant OS
- **Hardware**: [Your hardware details]
- **Static IP**: 192.168.1.146:8123

## Installed Add-ons
- InfluxDB
- Node-RED
- Grafana
- Tailscale
- AdGuard Home
- Duck DNS
- Glances
- Mosquitto Broker
- Spotify Connect
- Studio Code Server

## Connected Devices
- Multiple SONOFF devices
- TUYA devices
- 2x 8kW Sunsynk inverters
- [Add other devices as needed]

## Security Notes
- All sensitive information is stored in `secrets.yaml` (not committed)
- Use `secrets.yaml.example` as a template
- Database files and logs are excluded from version control

## Installation
1. Copy `secrets.yaml.example` to `secrets.yaml`
2. Fill in your actual values in `secrets.yaml`
3. Restart Home Assistant

## Backup Strategy
- Local backups configured
- Cloud backups enabled
- Configuration versioned in Git

## Support
For issues with this configuration, please create an issue in this repository.