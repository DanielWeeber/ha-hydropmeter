"""Plausibilitätsfilter für Zählerstände (ohne Home-Assistant-Abhängigkeiten, testbar).

Hintergrund: Die Hydrop-Kamera liest Ziffern gelegentlich falsch (z. B. 409 als 499).
Ein solcher Ausreißer nach oben und der Rücksprung danach werden vom Energie-Dashboard
(state_class total_increasing) doppelt als Verbrauch gezählt (Vorfall 12.04.2026: +499 m³).

Regeln:
- Ein Wert ist plausibel, wenn er gegenüber dem letzten akzeptierten Wert nicht fällt und
  höchstens um max_flow_m3h * vergangene Stunden (+ Toleranz) steigt.
- Unplausible Werte werden verworfen; nach außen bleibt der letzte akzeptierte Wert stehen
  (kleine Rücksprünge durch Lesefehler verschwinden damit ebenfalls).
- Bleibt ein neues Niveau über confirm_seconds stabil (z. B. Zählertausch), wird es übernommen.
"""
from __future__ import annotations

from dataclasses import dataclass

DEFAULT_TOLERANCE_M3 = 0.05


@dataclass
class _Pending:
    first_seen: float
    last_value: float
    last_seen: float


class MeterFilter:
    """Filtert unplausible Sprünge eines monoton steigenden Zählerstands."""

    def __init__(
        self,
        max_flow_m3h: float,
        confirm_seconds: float = 6 * 3600,
        tolerance_m3: float = DEFAULT_TOLERANCE_M3,
    ) -> None:
        self.max_flow_m3h = max_flow_m3h
        self.confirm_seconds = confirm_seconds
        self.tolerance_m3 = tolerance_m3
        self.value: float | None = None
        self.value_time: float | None = None
        self._pending: _Pending | None = None
        self.rejected_count = 0
        self.last_rejected: float | None = None

    def seed(self, value: float, at: float) -> None:
        """Startwert setzen (z. B. letzter Zustand vor dem HA-Neustart)."""
        if self.value is None:
            self.value = value
            self.value_time = at

    def _plausible(self, base: float, base_time: float, value: float, now: float) -> bool:
        hours = max(now - base_time, 0.0) / 3600
        delta = value - base
        return 0.0 <= delta <= self.max_flow_m3h * hours + self.tolerance_m3

    def process(self, value: float, now: float) -> tuple[float, bool]:
        """Rohwert prüfen. Rückgabe: (Wert nach außen, akzeptiert?)."""
        if self.value is None or self.value_time is None:
            self.value, self.value_time = value, now
            return value, True

        if self._plausible(self.value, self.value_time, value, now):
            self.value, self.value_time = value, now
            self._pending = None
            return value, True

        # Unplausibel: als möglichen neuen Stand vormerken
        p = self._pending
        if p is not None and self._plausible(p.last_value, p.last_seen, value, now):
            p.last_value, p.last_seen = value, now
            if now - p.first_seen >= self.confirm_seconds:
                self.value, self.value_time = value, now
                self._pending = None
                return value, True
        else:
            self._pending = _Pending(first_seen=now, last_value=value, last_seen=now)

        self.rejected_count += 1
        self.last_rejected = value
        return self.value, False
