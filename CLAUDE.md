# CLAUDE.md – Entwickler-Gedächtnis für ha-hydropmeter

Diese Datei dient als persistentes Gedächtnis für Claude (KI-Assistent).
Sie enthält wichtige Konventionen und Prozesse, die bei jeder Arbeit an diesem Repo beachtet werden müssen.

---

## Repository-Übersicht

HVAC/Wasser-Integration für Home Assistant zum Auslesen des **Hydrop Systems Wasserzählers** via Cloud API.

- **Domain:** `hydropmeter`
- **API:** `https://hydrop-systems.com/api/v1/device/{sensor_name}/newest` (Header: `apikey`)
- **Plattformen:** `sensor`
- **Sprache:** Deutsch (Kommentare & Strings)

### Wichtige Dateien

| Datei | Inhalt |
|---|---|
| `custom_components/hydropmeter/manifest.json` | **Versionsnummer** – muss bei jedem Release erhöht werden |
| `custom_components/hydropmeter/const.py` | `VERSION` Konstante – muss synchron mit manifest.json gehalten werden |
| `CHANGELOG.md` | Menschenlesbare Versionshistorie |
| `hacs.json` | HACS-Konfiguration |

---

## Release-Prozess (PFLICHT bei jeder neuen Version)

Damit der **Changelog im Home Assistant Update-Dialog erscheint**, muss zu jeder neuen Version ein **GitHub Release** erstellt werden. HACS liest den Changelog direkt aus dem Release Body des entsprechenden Git-Tags.

### Schritt-für-Schritt

1. **`manifest.json` aktualisieren**
   ```json
   { "version": "X.Y.Z" }
   ```

2. **`const.py` aktualisieren** (falls `VERSION` dort definiert ist)
   ```python
   VERSION = "X.Y.Z"
   ```

3. **`CHANGELOG.md` aktualisieren**
   - Neuen Abschnitt `## [X.Y.Z] - YYYY-MM-DD` ganz oben einfügen
   - Änderungen unter `### Added`, `### Changed`, `### Fixed`, `### Removed` kategorisieren

4. **Commit & Push**
   ```bash
   git add .
   git commit -m "release: bump version to X.Y.Z"
   git push
   ```

5. **GitHub Release erstellen** ← DAS IST DER SCHLÜSSEL FÜR DEN HA-CHANGELOG
   - Tag: `vX.Y.Z` (z.B. `v1.1.0`)
   - Release Title: `vX.Y.Z`
   - Release Body: **Den Inhalt des neuen Changelog-Abschnitts aus `CHANGELOG.md` einfügen**
   - Via GitHub API (wenn Claude das übernimmt):
     ```
     mcp__github__create_release(
       owner="DanielWeeber",
       repo="ha-hydropmeter",
       tag="vX.Y.Z",
       name="vX.Y.Z",
       body="<changelog text>"
     )
     ```

### Warum das wichtig ist

HACS zeigt den Changelog im HA Update-Dialog an, indem es den **GitHub Release Body** des neuen Tags liest. Ohne ein GitHub Release (auch wenn der Code-Tag existiert) erscheint **kein Changelog** für den Nutzer.

---

## Semantic Versioning

- `MAJOR` (X.0.0): Breaking changes (z.B. inkompatible Konfigurationsänderungen)
- `MINOR` (0.X.0): Neue Features (rückwärtskompatibel)
- `PATCH` (0.0.X): Bugfixes

---

## Entwicklungskonventionen

- Kommentare und Log-Meldungen auf **Deutsch**
- Kein `requirements` in manifest.json (nur stdlib + HA-builtins)
- `entry.options` hat immer Vorrang vor `entry.data` (Options-Flow-Änderungen wirken sofort nach Reload)
- Flow-Sensor-Berechnung: Delta m³ / Delta Stunden, nur bei `delta_m3 >= 0` (kein negativer Verbrauch)
