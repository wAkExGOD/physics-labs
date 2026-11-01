from pathlib import Path
import json
import math
import tempfile
import unittest
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lab5_model as m


class ModelTests(unittest.TestCase):
    def test_relativistic_wavelength_from_energy_momentum(self):
        for voltage in (30, 40, 60, 120):
            kinetic = m.E*voltage*1000
            rest = m.M*m.C**2
            momentum = math.sqrt((rest+kinetic)**2-rest**2)/m.C
            self.assertAlmostEqual(float(m.wavelength_a(voltage)), m.H/momentum*1e10, places=13)
        self.assertLess(m.wavelength_a(120), m.wavelength_a(30))

    def test_ring_positions_and_second_order(self):
        r = m.ring_radii_mm(30)
        np.testing.assert_allclose((r[:5]/r[0])**2, [1, 2, 3, 4, 5], rtol=1e-14)
        self.assertAlmostEqual(r[3], 2*r[0])

    def test_animation_partition_does_not_change_points(self):
        a = m.ElectronSimulation(m.Configuration(40, 123))
        b = m.ElectronSimulation(m.Configuration(40, 123))
        a.add(10000)
        for count in (1, 7, 0, 119, 83, 5000, 4790):
            b.add(count)
        np.testing.assert_array_equal(a.points, b.points)

    def test_session_roundtrip_preserves_rng(self):
        a = m.ElectronSimulation(m.Configuration(60, 456))
        a.add(300)
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as directory:
            file = Path(directory)/"series.json"
            a.save(file)
            b = m.ElectronSimulation.load(file)
            a.add(50)
            b.add(50)
            np.testing.assert_array_equal(a.points, b.points)
            data = json.loads(file.read_text(encoding="utf-8"))
            data["points"][0][2] = 9
            file.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                m.ElectronSimulation.load(file)

    def test_conditional_denominator_excludes_direct_beam(self):
        sim = m.ElectronSimulation()
        sim.points = np.array([[0, 0, 0], [1, 0, 1], [2, 0, 2], [0, 0, 0], [1, 0, 1]], dtype=float)
        row = sim.history(5)[-1]
        np.testing.assert_allclose(row, [5, 3, 2/3, 1/3])
        sim.points[:, 2] = 0
        self.assertTrue(np.isnan(sim.history(5)[-1, 2:]).all())

    def test_measured_radii_use_coordinates(self):
        sim = m.ElectronSimulation(m.Configuration(30, 9))
        sim.add(10000)
        first = m.measured_radii(sim)
        sim.points[:, 2] = 0
        self.assertEqual(first, m.measured_radii(sim))

    def test_structure_recovers_indices_with_required_orders(self):
        rows = m.analyze_structure(m.ring_radii_mm(30)[:5])
        self.assertEqual([row["rounded_sum"] for row in rows], [2, 4, 6, 2, 10])
        self.assertEqual([row["allowed_bcc"][0] for row in rows], list(m.HKL[:5]))
        self.assertTrue(all(not row["warning"] for row in rows))

    def test_invalid_inputs_and_extreme_indices(self):
        for value in ("", "abc", "nan", "inf", 0, -1):
            with self.assertRaises(ValueError):
                m.finite_number(value, "V", 1, 300)
        self.assertEqual(m.finite_number("30,5", "V", 1, 300), 30.5)
        with self.assertRaises(ValueError):
            m.analyze_structure([1, 2, 3, 3, 5])
        self.assertEqual(m.miller_candidates(10**12), [])
        # Верхняя граница разрешённого seed должна работать и в сериях с подсеменами.
        self.assertEqual(len(m.voltage_experiment(1000, 2**32-1)["rows"]), 6)

    def test_prescribed_probabilities_and_radial_scales(self):
        sim = m.ElectronSimulation(m.Configuration(40, 8))
        sim.add(100000)
        expected = 100000*m.CHANNEL_PROBABILITIES
        sigma = np.sqrt(100000*m.CHANNEL_PROBABILITIES*(1-m.CHANNEL_PROBABILITIES))
        self.assertTrue(np.all(abs(sim.counts()-expected) < 6*sigma))
        centers = m.ring_radii_mm(40)
        for j, row in enumerate(m.measured_radii(sim)):
            self.assertLess(abs(row["radius_mm"]-centers[j]), 6*row["sem_mm"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
