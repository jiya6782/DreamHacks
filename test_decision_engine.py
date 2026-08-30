import unittest

from decision_engine import (
    build_decision,
    energy_potential,
    detect_environmental_event,
)


class DecisionEngineTests(unittest.TestCase):

    def setUp(self):

        self.environment = {
            "solar_radiation": 850,
            "wind_speed": 4,
            "temperature": 28,
            "rainfall": 0,
            "weather": "Clear",
            "time_of_day": "12:00",
        }


    # --------------------------------------------------
    # ENERGY
    # --------------------------------------------------

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


    # --------------------------------------------------
    # WATER / HEAT
    # --------------------------------------------------

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


    # --------------------------------------------------
    # LOW ENERGY
    # --------------------------------------------------

    def test_low_conditions_recommend_conservation(self):

        result = build_decision(
            {
                **self.environment,
                "solar_radiation": 100,
                "wind_speed": 2,
            },
            [
                {
                    "name": "Water",
                    "quantity": 10,
                    "unit": "L",
                    "priority": 10,
                }
            ],
        )

        energy_recommendations = [
            r
            for r in result["recommendations"]
            if r["type"] == "energy"
        ]

        self.assertTrue(
            any(
                "Conserve" in r["title"]
                for r in energy_recommendations
            )
        )


    # --------------------------------------------------
    # STORM DETECTION
    # --------------------------------------------------

    def test_storm_is_detected(self):

        environment = {
            **self.environment,
            "wind_speed": 15,
            "rainfall": 12,
            "weather": "Storm",
        }

        result = detect_environmental_event(
            environment
        )

        self.assertEqual(
            result["event"],
            "Storm",
        )

        self.assertEqual(
            result["severity"],
            "Critical",
        )


    # --------------------------------------------------
    # HEATWAVE DETECTION
    # --------------------------------------------------

    def test_heatwave_is_detected(self):

        environment = {
            **self.environment,
            "temperature": 31,
            "solar_radiation": 950,
        }

        result = detect_environmental_event(
            environment
        )

        self.assertEqual(
            result["event"],
            "Heatwave",
        )


    # --------------------------------------------------
    # STORM CHANGES PRIORITIES
    # --------------------------------------------------

    def test_storm_promotes_shelter(self):

        environment = {
            **self.environment,
            "wind_speed": 15,
            "rainfall": 12,
            "weather": "Storm",
        }

        resources = [

            {
                "name": "Food Stores",
                "category": "Food",
                "quantity": 1000,
                "unit": "meals",
                "priority": 7,
            },

            {
                "name": "Emergency Shelter",
                "category": "General",
                "quantity": 24,
                "unit": "spaces",
                "priority": 5,
            },

        ]

        result = build_decision(
            environment,
            resources,
        )

        self.assertEqual(
            result["event"]["event"],
            "Storm",
        )

        self.assertEqual(
            result["resources"][0]["name"],
            "Emergency Shelter",
        )


    # --------------------------------------------------
    # HEATWAVE CHANGES PRIORITIES
    # --------------------------------------------------

    def test_heatwave_promotes_water(self):

        environment = {
            **self.environment,
            "temperature": 31,
            "solar_radiation": 950,
        }

        resources = [

            {
                "name": "Food Stores",
                "category": "Food",
                "quantity": 1000,
                "unit": "meals",
                "priority": 7,
            },

            {
                "name": "Fresh Water",
                "category": "Water",
                "quantity": 1000,
                "unit": "liters",
                "priority": 5,
            },

        ]

        result = build_decision(
            environment,
            resources,
        )

        self.assertEqual(
            result["event"]["event"],
            "Heatwave",
        )

        self.assertEqual(
            result["resources"][0]["name"],
            "Fresh Water",
        )


    # --------------------------------------------------
    # NORMAL CONDITIONS
    # --------------------------------------------------

    def test_normal_conditions_are_detected(self):

        result = detect_environmental_event(
            self.environment
        )

        self.assertEqual(
            result["event"],
            "Normal Conditions",
        )


if __name__ == "__main__":
    unittest.main()