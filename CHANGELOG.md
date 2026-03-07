# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2025-05-01

### Added
- Initial release of the Hydropmeter Home Assistant integration
- Water meter sensor (m³, total_increasing, compatible with Energy Dashboard)
- Optional flow rate sensor (m³/h, calculated from consecutive readings)
- Config Flow for easy setup via the HA UI
- Options Flow to change API key, sensor name, scan interval and flow sensor toggle at runtime without re-setup
- Full German translation
