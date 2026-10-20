# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-10-20

### Added
- Plausibility filter for meter readings: values that drop or rise faster than the new option "Plausibility limit flow rate" (default 5 m³/h) are treated as camera misreads and ignored; the last valid value is kept. A new level that stays stable for 6 hours (e.g. meter replacement) is accepted.
- New option `max_flow` in setup and options dialog.
- Attributes `raw_value` and `rejected_readings` on the meter sensor.
- Unit tests for the filter (`python3 -m unittest discover -s tests`).

### Fixed
- A single misread (e.g. 409 read as 499 m³) and the jump back no longer count as hundreds of m³ in the Energy Dashboard (incident 2026-04-12: +499 m³ phantom consumption).
- The flow rate sensor only uses accepted readings.

---

## [1.0.4] - 2026-03-07

### Fixed
- Removed model field from device info that was displayed as unwanted text under the device entry

---

## [1.0.3] - 2026-03-07

### Fixed
- Removed attribution text that was incorrectly displayed below entity cards

---

## [1.0.2] - 2026-03-07

### Changed
- Service Info card: version, manufacturer and integration author are now shown as separate fields instead of one long string
  - **Firmware version:** `v1.0.2`
  - **Manufacturer:** Hydrop Systems – hydrop-systems.com
  - **Model:** Integration by Daniel Weeber (github.com/DanielWeeber)

---

## [1.0.1] - 2026-03-07

### Added
- Automated GitHub Release workflow via GitHub Actions
- `CHANGELOG.md` for version history
- `CLAUDE.md` as persistent memory for the release process

### Fixed
- Flow rate sensor now shows `0 m³/h` instead of `Unknown` when no value is available yet

---

## [1.0.0] - 2025-05-01

### Added
- Initial release of the Hydropmeter Home Assistant integration
- Water meter sensor (m³, total_increasing, compatible with Energy Dashboard)
- Optional flow rate sensor (m³/h, calculated from consecutive readings)
- Config Flow for easy setup via the HA UI
- Options Flow to change API key, sensor name, scan interval and flow sensor toggle at runtime without re-setup
- Full German translation
