"""Tests für den Plausibilitätsfilter (ohne Home Assistant lauffähig).

Aufruf: python3 -m unittest discover -s tests
"""
import importlib.util
import pathlib
import sys
import unittest

_spec = importlib.util.spec_from_file_location(
    "meter_filter",
    pathlib.Path(__file__).parents[1] / "custom_components/hydropmeter/meter_filter.py",
)
meter_filter = importlib.util.module_from_spec(_spec)
sys.modules["meter_filter"] = meter_filter
_spec.loader.exec_module(meter_filter)
MeterFilter = meter_filter.MeterFilter

MIN = 60.0


class MeterFilterTest(unittest.TestCase):
    def test_normaler_verbrauch(self):
        f = MeterFilter(max_flow_m3h=5)
        self.assertEqual(f.process(100.0, 0), (100.0, True))
        self.assertEqual(f.process(100.2, 5 * MIN), (100.2, True))

    def test_vorfall_april_ausreisser_und_ruecksprung(self):
        # 12.04.2026: 409.998 -> 499.02 (Fehllesung) -> 410.07
        f = MeterFilter(max_flow_m3h=5)
        f.process(409.9983, 0)
        out, ok = f.process(499.0207, 5 * MIN)
        self.assertFalse(ok)
        self.assertEqual(out, 409.9983)
        out, ok = f.process(499.0207, 60 * MIN)
        self.assertFalse(ok)
        out, ok = f.process(410.0694, 65 * MIN)
        self.assertTrue(ok)
        self.assertEqual(out, 410.0694)

    def test_kleiner_ruecksprung_wird_gehalten(self):
        f = MeterFilter(max_flow_m3h=5)
        f.process(409.7014, 0)
        out, ok = f.process(409.6054, 5 * MIN)
        self.assertFalse(ok)
        self.assertEqual(out, 409.7014)
        self.assertEqual(f.process(409.7054, 10 * MIN), (409.7054, True))

    def test_stabiles_neues_niveau_wird_uebernommen(self):
        # Zählertausch: neuer Zähler startet bei 0 und steigt langsam
        f = MeterFilter(max_flow_m3h=5, confirm_seconds=6 * 3600)
        f.process(500.0, 0)
        t, v = 0.0, 0.0
        accepted = False
        while t < 7 * 3600:
            t += 5 * MIN
            v += 0.001
            out, accepted = f.process(v, t)
            if accepted:
                break
        self.assertTrue(accepted)
        self.assertGreaterEqual(t, 6 * 3600)
        self.assertAlmostEqual(out, v)

    def test_seed_verhindert_sprung_nach_neustart(self):
        f = MeterFilter(max_flow_m3h=5)
        f.seed(409.99, 0)
        self.assertEqual(f.process(499.02, 5 * MIN), (409.99, False))

    def test_lange_pause_erlaubt_groesseren_anstieg(self):
        f = MeterFilter(max_flow_m3h=5)
        f.process(100.0, 0)
        self.assertTrue(f.process(101.0, 24 * 3600)[1])


if __name__ == "__main__":
    unittest.main()
