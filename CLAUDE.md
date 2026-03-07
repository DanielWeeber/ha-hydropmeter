# CLAUDE.md – Entwickler-Gedächtnis für ha-hydropmeter

Diese Datei dient als persistentes Gedächtnis für Claude (KI-Assistent).
Sie enthält wichtige Konventionen und Prozesse, die bei jeder Arbeit an diesem Repo beachtet werden müssen.

---

## Repository-Übersicht

HA-Integration zum Auslesen des **Hydrop Systems Wasserzählers** via Cloud API.

- **Domain:** `hydropmeter`
- **API:** `https://hydrop-systems.com/api/v1/device/{sensor_name}/newest` (Header: `apikey`)
- **Plattformen:** `sensor`
- **Sprache:** Deutsch (Kommentare & Strings)

### Wichtige Dateien

| Datei | Inhalt |
|---|---|
| `custom_components/hydropmeter/manifest.json` | **Versionsnummer** – einziger Trigger für den Auto-Release |
| `custom_components/hydropmeter/const.py` | `VERSION`-Konstante – muss synchron mit manifest.json gehalten werden |
| `CHANGELOG.md` | Menschenlesbare Versionshistorie |
| `.github/workflows/release.yml` | GitHub Action für automatische Releases |

---

## Release-Prozess

### Vollautomatisch – nur 2 Dateien pushen

Der Release (GitHub Release + Tag + Changelog im HA Update-Dialog) wird **vollautomatisch** durch die GitHub Action `.github/workflows/release.yml` erstellt, sobald `manifest.json` mit einer neuen Version auf `main` gepusht wird.

**Das bedeutet: Ich (Claude) muss nur diese zwei Dateien ändern und pushen — alles andere läuft von selbst.**

#### Schritt 1: `manifest.json` – Versionsnummer erhöhen
```json
{ "version": "X.Y.Z" }
```

#### Schritt 2: `CHANGELOG.md` – neuen Abschnitt ganz oben einfügen
```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- ...

### Fixed
- ...
```

#### Schritt 3: Beide Dateien in einem Commit pushen
```python
mcp__github__push_files(
    owner="DanielWeeber",
    repo="ha-hydropmeter",
    branch="main",
    message="release: bump version to X.Y.Z",
    files=[
        {"path": "custom_components/hydropmeter/manifest.json", "content": "..."},
        {"path": "CHANGELOG.md", "content": "..."},
        # Optional: const.py wenn VERSION dort auch definiert ist
    ]
)
```

**Fertig.** Die GitHub Action liest automatisch den passenden Changelog-Block aus `CHANGELOG.md` und erstellt den Release mit dem korrekten Tag `vX.Y.Z`.

### Was die Action macht (zur Information)

1. Erkennt die neue Version aus `manifest.json`
2. Prüft ob der Release-Tag bereits existiert (verhindert Duplikate)
3. Extrahiert den passenden Block aus `CHANGELOG.md`
4. Erstellt den GitHub Release mit Tag `vX.Y.Z` und dem Changelog als Body

---

## Semantic Versioning

- `MAJOR` (X.0.0): Breaking changes (z.B. inkompatible Konfiguration)
- `MINOR` (0.X.0): Neue Features (rückwärtskompatibel)
- `PATCH` (0.0.X): Bugfixes

---

## Entwicklungskonventionen

- Kommentare und Log-Meldungen auf **Deutsch**
- Kein `requirements` in manifest.json (nur stdlib + HA-builtins)
- `entry.options` hat Vorrang vor `entry.data` (Options-Flow-Änderungen wirken sofort)
- Flow-Sensor-Berechnung: Delta m³ / Delta Stunden, nur bei `delta_m3 >= 0`
- Durchfluss-Sensor gibt `0.0 m³/h` zurück wenn kein Wert vorliegt (nicht `None`/Unknown)
