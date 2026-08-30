"""Deterministic environmental data source for the island simulation."""

from datetime import datetime, timedelta
from typing import Any, Dict


class EnvironmentalSimulator:

    def __init__(self, start=None):

        self.current = start or datetime(
            2025,
            6,
            21,
            9,
            0,
        )

        self.step = 0

    def snapshot(self) -> Dict[str, Any]:

        hour = (
            self.current.hour
            + self.current.minute / 60
        )

        # --------------------------------------------------
        # DAYLIGHT
        # --------------------------------------------------

        daylight = max(
            0,
            1 - abs(hour - 12) / 7,
        )

        # --------------------------------------------------
        # CLOUD CYCLE
        # --------------------------------------------------

        cloud_cycle = (
            self.step % 5
        ) / 4

        # --------------------------------------------------
        # SOLAR
        # --------------------------------------------------

        solar = round(
            max(
                0,
                930
                * daylight
                * (
                    1
                    - 0.28 * cloud_cycle
                ),
            )
        )

        # --------------------------------------------------
        # WIND
        # --------------------------------------------------

        wind = round(
            9
            + 4 * ((self.step + 1) % 3)
            - 2 * cloud_cycle,
            1,
        )

        # --------------------------------------------------
        # TEMPERATURE
        # --------------------------------------------------

        temperature = round(
            22
            + 7 * daylight
            - cloud_cycle * 2,
            1,
        )

        # --------------------------------------------------
        # RAINFALL
        # --------------------------------------------------
        #
        # Every few simulation steps the island enters
        # a rainfall period. This gives the decision engine
        # another sensor to analyze.
        #
        # Steps 6-7 create a storm-like period.
        # --------------------------------------------------

        storm_cycle = self.step % 10

        if storm_cycle in [6, 7]:

            rainfall = round(
                8 + storm_cycle * 0.8,
                1,
            )

            weather = "Storm"

        elif storm_cycle == 8:

            rainfall = 5.0
            weather = "Rain"

        else:

            rainfall = 0.0

            weather = (
                "Clear"
                if cloud_cycle < 0.4
                else "Partly cloudy"
                if cloud_cycle < 0.8
                else "Cloudy"
            )

        # --------------------------------------------------
        # HEATWAVE SIMULATION
        # --------------------------------------------------
        #
        # Steps 2-4 represent an unusually hot period.
        # This is still detected by environmental conditions
        # in decision_engine.py rather than directly by
        # the simulator.
        # --------------------------------------------------

        if self.step in [2, 3, 4]:

            temperature = round(
                temperature + 3,
                1,
            )

            solar = max(
                solar,
                850,
            )

        # --------------------------------------------------
        # RETURN SENSOR DATA
        # --------------------------------------------------

        return {
            "timestamp": self.current.isoformat(
                timespec="minutes"
            ),

            "time_of_day": self.current.strftime(
                "%H:%M"
            ),

            "solar_radiation": solar,

            "wind_speed": wind,

            "temperature": temperature,

            "rainfall": rainfall,

            "weather": weather,
        }

    def advance(self) -> None:

        self.step += 1

        self.current += timedelta(
            hours=1
        )