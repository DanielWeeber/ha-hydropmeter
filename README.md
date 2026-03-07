# 💧 Hydropmeter – Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Version](https://img.shields.io/badge/Version-1.0.0-blue.svg)](https://github.com/DanielWeeber/ha-hydropmeter/releases)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2023.x%2B-green.svg)](https://www.home-assistant.io/)

Diese Integration verbindet den **Hydrop Systems Hydropmeter** Wasserzähler-Aufsatz mit Home Assistant. Der aktuelle Wasserverbrauch wird automatisch als Sensor bereitgestellt und kann direkt ins Energie-Dashboard eingebunden werden.

---

## Was ist der Hydropmeter?

Der [Hydropmeter von Hydrop Systems](https://hydrop-systems.com) ist ein Aufsatz für herkömmliche Wasserzähler. Er liest den Zählerstand optisch aus und überträgt ihn per WLAN an die Cloud-API. Diese Integration holt den Wert regelmäßig ab und stellt ihn als `sensor` in Home Assistant bereit.

---

## Funktionen

- Aktuellen Wasserverbrauch als Sensor mit der Einheit **m³**
- Vollständige Kompatibilität mit dem **Energie-Dashboard** (device_class: water, state_class: total_increasing)
- Konfiguration komplett über die **Benutzeroberfläche** (kein YAML erforderlich)
- Einstellbares Abfrageintervall (Standard: alle 5 Minuten)
- Automatische Fehlerbehandlung bei Verbindungsproblemen
- Optional: **Durchflussrate** über HA-eigene Derivative-Helfer (m³/h, L/min)

---

## Installation über HACS (empfohlen)

1. Öffne HACS in Home Assistant.
2. Klicke auf **Integrationen** → Drei-Punkte-Menü oben rechts → **Benutzerdefinierte Repositories**.
3. Füge folgende URL hinzu:
   ```
   https://github.com/DanielWeeber/ha-hydropmeter
   ```
   Kategorie: **Integration**
4. Suche nach **Hydropmeter** und klicke auf **Herunterladen**.
5. Starte Home Assistant neu.

---

## Manuelle Installation

1. Lade die [neueste Version](https://github.com/DanielWeeber/ha-hydropmeter/releases/latest) herunter.
2. Kopiere den Ordner `custom_components/hydropmeter` in dein Home Assistant Konfigurationsverzeichnis unter `custom_components/`.
3. Starte Home Assistant neu.

---

## Einrichtung

1. Gehe zu **Einstellungen → Geräte & Dienste → Integration hinzufügen**.
2. Suche nach **Hydropmeter**.
3. Fülle die Felder aus:

| Feld | Beschreibung | Beispiel |
|------|-------------|---------|
| **Anzeigename** | Name des Sensors in HA | `Wasserzähler` |
| **Sensor-Name (URL-Teil)** | Name des Sensors in der API-URL | `Wasserzähler` |
| **API-Schlüssel** | Dein persönlicher API-Key von Hydrop Systems | `8pf4wSMGj...` |
| **Eindeutige ID** | Interne ID der HA-Entität (Standard ist meistens ausreichend) | `wasserzaehler_hydrop` |
| **Abfrageintervall** | Sekunden zwischen den API-Abfragen (min. 60) | `300` |

> **Tipp:** Den API-Schlüssel findest du in der Hydrop App oder in deinen Account-Einstellungen auf [hydrop-systems.com](https://hydrop-systems.com).

---

## Energie-Dashboard einrichten

Nachdem der Sensor eingerichtet ist:

1. Gehe zu **Energie → Energie-Dashboard → Konfigurieren**.
2. Wähle unter **Wasserverbrauch** die Option **Wasserverbrauch hinzufügen**.
3. Wähle den Hydropmeter-Sensor aus.

---

## Durchflussrate (optional)

Die Integration liefert den Gesamtzählerstand (m³). Um daraus eine Durchflussrate in **m³/h** oder **L/min** zu erhalten, kannst du HA's eingebauten **Derivative-Helfer** verwenden:

### Durchfluss in m³/h

1. Gehe zu **Einstellungen → Geräte & Dienste → Helfer → Helfer erstellen**.
2. Wähle **Ableitung eines Sensors** (Derivative).
3. Konfiguriere:

| Einstellung | Wert |
|------------|------|
| Name | `Wasserzähler Durchfluss` |
| Eingabe-Sensor | dein Hydropmeter-Sensor (z. B. `sensor.wasserzahler`) |
| Zeiteinheit | `Stunden (h)` |
| Genauigkeit | `4` |

→ Ergebnis: Sensor mit Einheit **m³/h**

### Durchfluss in L/min

Erstelle einen weiteren Derivative-Helfer mit:

| Einstellung | Wert |
|------------|------|
| Name | `Wasserzähler Durchfluss Minuten` |
| Eingabe-Sensor | dein Hydropmeter-Sensor |
| Zeiteinheit | `Minuten (min)` |
| Genauigkeit | `4` |

Das ergibt **m³/min**. Für **L/min** erstelle anschließend einen Template-Sensor:

```yaml
# configuration.yaml
template:
  - sensor:
      - name: "Wasserzähler Durchfluss L/min"
        unit_of_measurement: "L/min"
        device_class: volume_flow_rate
        state_class: measurement
        state: "{{ (states('sensor.wasserzahler_durchfluss_minuten') | float(0) * 1000) | round(2) }}"
```

> **Hinweis:** Die Derivative-Sensoren zeigen erst nach dem zweiten Abruf-Zyklus einen Wert (da eine Differenz benötigt wird). Bei einem Abfrageintervall von 5 Minuten kann es bis zu 10 Minuten dauern.

---

## Technische Details

- **API-Endpunkt:** `https://api.hydrop-systems.com/sensors/ID/{sensor_name}/newest`
- **Authentifizierung:** API-Key im HTTP-Header (`apikey`)
- **Abgerufene Werte:** `meterValue` (Zählerstand in m³), `timestamp`
- **Aktualisierung:** Per `DataUpdateCoordinator` (async, ressourcenschonend)

---

## Fehlerbehebung

**Sensor zeigt "Nicht verfügbar":**
- Sensor-Name in der Konfiguration prüfen (muss exakt mit dem API-URL-Teil übereinstimmen).
- API-Schlüssel auf Gültigkeit prüfen.
- Logs unter **Einstellungen → System → Protokolle** auf Fehler prüfen.

**Verbindung fehlgeschlagen (404):**
- Der Sensor-Name muss exakt dem entsprechen, der in der API-URL verwendet wird (Umlaute sind kein Problem).

**Ungültiger API-Schlüssel (401):**
- Den API-Key in der Hydrop App neu generieren und die Integration neu konfigurieren.

---

## Lizenz

MIT License – siehe [LICENSE](LICENSE)

---

## Beitragen

Pull Requests und Issues sind willkommen unter [github.com/DanielWeeber/ha-hydropmeter](https://github.com/DanielWeeber/ha-hydropmeter).
