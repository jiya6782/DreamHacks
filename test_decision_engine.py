import unittest

from decision_engine import (
    build_decision,
    detect_event,
    energy_potential,
)


class DecisionEngineTests(unittest.TestCase):

    def setUp(self):

        self.environment = {
            "solar_radiation": 900,
            "wind_speed": 4,
            "temperature": 28,
            "weather": "Clear",
            "time_of_day": "12:00",
        }

    # ======================================================
    # ENERGY TESTS
    # ======================================================

    def test_energy_uses_solar_and_wind(self):

        result = energy_potential(
            self.environment
        )

        self.assertEqual(
            result["solar_level"],
            "High",
        )

        self.assertGreater(
            result["total_kw"],
            result["solar_kw"],
        )

    # ======================================================
    # WATER PRIORITY TEST
    # ======================================================

    def test_priority_and_heat_can_promote_water(self):

        resources = [
            {
                "name": "Food",
                "quantity": 1000,
                "unit": "kg",
                "priority": 7,
            },

            {
                "name": "Water",
                "quantity": 420,
                "unit": "L",
                "priority": 10,
            },
        ]

        result = build_decision(
            self.environment,
            resources,
        )

        self.assertEqual(
            result["resources"][0]["name"],
            "Water",
        )

    # ======================================================
    # LOW ENERGY TEST
    # ======================================================

    def test_low_conditions_recommend_conservation(self):

        environment = {
            **self.environment,
            "solar_radiation": 100,
            "wind_speed": 2,
        }

        result = build_decision(
            environment,
            [
                {
                    "name": "Water",
                    "quantity": 10,
                    "unit": "L",
                    "priority": 10,
                }
            ],
        )

        energy_types = [
            recommendation["type"]
            for recommendation
            in result["recommendations"]
        ]

        self.assertIn(
            "energy",
            energy_types,
        )

    # ======================================================
    # STORM DETECTION
    # ======================================================

    def test_storm_detection(self):

        storm_environment = {
            "solar_radiation": 280,
            "wind_speed": 16,
            "temperature": 23,
            "weather": "Heavy rain",
            "time_of_day": "14:00",
        }

        result = detect_event(
            storm_environment
        )

        self.assertEqual(
            result["event"],
            "Storm",
        )

        self.assertEqual(
            result["severity"],
            "High",
        )

        self.assertGreaterEqual(
            result["confidence"],
            70,
        )

    # ======================================================
    # HEATWAVE DETECTION
    # ======================================================

    def test_heatwave_detection(self):

        heat_environment = {
            "solar_radiation": 1050,
            "wind_speed": 4,
            "temperature": 35,
            "weather": "Clear",
            "time_of_day": "13:00",
        }

        result = detect_event(
            heat_environment
        )

        self.assertEqual(
            result["event"],
            "Heatwave",
        )

        self.assertEqual(
            result["severity"],
            "High",
        )

    # ======================================================
    # HIGH WIND DETECTION
    # ======================================================

    def test_high_wind_detection(self):

        wind_environment = {
            "solar_radiation": 500,
            "wind_speed": 14,
            "temperature": 25,
            "weather": "Cloudy",
            "time_of_day": "15:00",
        }

        result = detect_event(
            wind_environment
        )

        self.assertEqual(
            result["event"],
            "High Wind",
        )

    # ======================================================
    # NORMAL CONDITIONS
    # ======================================================

    def test_normal_conditions(self):

        normal_environment = {
            "solar_radiation": 600,
            "wind_speed": 6,
            "temperature": 25,
            "weather": "Clear",
            "time_of_day": "12:00",
        }

        result = detect_event(
            normal_environment
        )

        self.assertEqual(
            result["event"],
            "Normal",
        )

    # ======================================================
    # STORM CHANGES RESOURCE PRIORITIES
    # ======================================================

    def test_storm_changes_priorities(self):

        storm_environment = {
            "solar_radiation": 280,
            "wind_speed": 16,
            "temperature": 23,
            "weather": "Heavy rain",
            "time_of_day": "14:00",
        }

        resources = [
            {
                "name": "Food Stores",
                "quantity": 126,
                "unit": "meals",
                "priority": 7,
            },

            {
                "name": "Shelter",
                "quantity": 50,
                "unit": "units",
                "priority": 5,
            },
        ]

        result = build_decision(
            storm_environment,
            resources,
        )

        shelter = next(
            resource
            for resource in result["resources"]
            if resource["name"] == "Shelter"
        )

        self.assertEqual(
            shelter["event_boost"],
            6,
        )

    # ======================================================
    # STORM CHANGES ENERGY ALLOCATION
    # ======================================================

    def test_storm_changes_energy_allocation(self):

        storm_environment = {
            "solar_radiation": 280,
            "wind_speed": 16,
            "temperature": 23,
            "weather": "Heavy rain",
            "time_of_day": "14:00",
        }

        resources = [
            {
                "name": "Fresh Water",
                "quantity": 1840,
                "unit": "liters",
                "priority": 10,
            }
        ]

        result = build_decision(
            storm_environment,
            resources,
        )

        allocations = result[
            "energy_allocation"
        ]

        emergency = next(
            allocation
            for allocation in allocations
            if "Emergency" in allocation["system"]
        )

        self.assertGreater(
            emergency["percent"],
            25,
        )


if __name__ == "__main__":
    unittest.main()