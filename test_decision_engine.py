import unittest

from decision_engine import build_decision, energy_potential


class DecisionEngineTests(unittest.TestCase):
    def setUp(self):
        self.environment = {"solar_radiation": 900, "wind_speed": 4, "temperature": 28, "weather": "Clear", "time_of_day": "12:00"}

    def test_energy_uses_solar_and_wind(self):
        result = energy_potential(self.environment)
        self.assertEqual(result["solar_level"], "High")
        self.assertGreater(result["total_kw"], result["solar_kw"])

    def test_priority_and_heat_can_promote_water(self):
        resources = [{"name": "Food", "quantity": 1000, "unit": "kg", "priority": 7}, {"name": "Water", "quantity": 420, "unit": "L", "priority": 10}]
        result = build_decision(self.environment, resources)
        self.assertEqual(result["resources"][0]["name"], "Water")
        self.assertIn("water", result["recommendations"][0]["title"])

    def test_low_conditions_recommend_conservation(self):
        result = build_decision({**self.environment, "solar_radiation": 100, "wind_speed": 2}, [{"name": "Water", "quantity": 10, "unit": "L", "priority": 10}])
        self.assertEqual(result["recommendations"][1]["type"], "energy")
        self.assertIn("Conserve", result["recommendations"][1]["title"])


if __name__ == "__main__":
    unittest.main()