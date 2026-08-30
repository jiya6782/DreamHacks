"""Deterministic environmental data source for the island simulation."""

from datetime import datetime, timedelta
from typing import Any, Dict


class EnvironmentalSimulator:

    def __init__(self, start=None):

        self.current = (
            start
            or datetime(2025, 6, 21, 9, 0)
        )

        self.step = 0

    # ======================================================
    # ENVIRONMENTAL SNAPSHOT
    # ======================================================

    def snapshot(self) -> Dict[str, Any]:

        scenario = self.step % 12

        # --------------------------------------------------
        # STORM
        # --------------------------------------------------

        if scenario in [3, 4]:

            solar = 280
            wind = 16
            temperature = 23
            weather = "Heavy rain"

        # --------------------------------------------------
        # HEATWAVE
        # --------------------------------------------------

        elif scenario in [7, 8]:

            solar = 1050
            wind = 4
            temperature = 35
            weather = "Clear"

        # --------------------------------------------------
        # HIGH WIND
        # --------------------------------------------------

        elif scenario == 10:

            solar = 500
            wind = 14
            temperature = 25
            weather = "Cloudy"

        # --------------------------------------------------
        # NORMAL CONDITIONS
        # --------------------------------------------------

        else:

            hour = (
                self.current.hour
                + self.current.minute / 60
            )

            daylight = max(
                0,
                1 - abs(hour - 12) / 7,
            )

            cloud_cycle = (
                self.step % 5
            ) / 4

            solar = round(
                max(
                    0,
                    930
                    * daylight
                    * (1 - 0.28 * cloud_cycle),
                )
            )

            wind = round(
                9
                + 4 * ((self.step + 1) % 3)
                - 2 * cloud_cycle,
                1,
            )

            temperature = round(
                22
                + 7 * daylight
                - cloud_cycle * 2,
                1,
            )

            weather = (
                "Clear"
                if cloud_cycle < 0.4
                else "Partly cloudy"
                if cloud_cycle < 0.8
                else "Cloudy"
            )

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

            "weather": weather,
        }

    # ======================================================
    # ADVANCE SIMULATION
    # ======================================================

    def advance(self) -> None:

        self.step += 1

        self.current += timedelta(
            hours=1
        )