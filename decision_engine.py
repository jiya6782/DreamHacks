"""Decision engine for the Isla resource management system.

Combines environmental conditions, detected environmental events,
resource levels, energy availability, and user priorities.
"""

from typing import Any, Dict


# ==========================================================
# ENERGY
# ==========================================================

def energy_potential(environment: Dict[str, Any]) -> Dict[str, Any]:
    """Estimate renewable energy production from current conditions."""

    solar_kw = round(
        environment["solar_radiation"] / 1000 * 4.0,
        2,
    )

    wind_kw = round(
        min(environment["wind_speed"] / 12, 1.5) * 1.8,
        2,
    )

    return {
        "solar_kw": solar_kw,
        "wind_kw": wind_kw,
        "total_kw": round(solar_kw + wind_kw, 2),

        "solar_level": (
            "High"
            if solar_kw >= 2.5
            else "Moderate"
            if solar_kw >= 1
            else "Low"
        ),

        "wind_level": (
            "High"
            if wind_kw >= 1.5
            else "Moderate"
            if wind_kw >= 0.8
            else "Low"
        ),
    }


# ==========================================================
# ENVIRONMENTAL EVENT DETECTION
# ==========================================================

def detect_event(environment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze multiple environmental signals and determine
    whether a significant environmental event is occurring.

    The system does not rely on one sensor alone. Instead,
    multiple signals contribute to an event confidence score.
    """

    solar = float(environment["solar_radiation"])
    wind = float(environment["wind_speed"])
    temperature = float(environment["temperature"])
    weather = str(environment["weather"]).lower()

    # ------------------------------------------------------
    # STORM
    # ------------------------------------------------------

    storm_score = 0
    storm_signals = []

    if wind >= 12:
        storm_score += 40
        storm_signals.append(
            f"High wind: {wind} m/s"
        )

    if "rain" in weather:
        storm_score += 35
        storm_signals.append(
            "Rain detected"
        )

    if "cloud" in weather or "storm" in weather:
        storm_score += 15
        storm_signals.append(
            "Heavy cloud cover"
        )

    if temperature <= 25:
        storm_score += 10
        storm_signals.append(
            f"Cool temperature: {temperature}°C"
        )

    if storm_score >= 70:
        return {
            "event": "Storm",
            "severity": "High",
            "confidence": min(storm_score, 100),
            "reason": (
                "Multiple environmental signals indicate "
                "that a storm is occurring or approaching."
            ),
            "signals": storm_signals,
        }

    # ------------------------------------------------------
    # HEATWAVE
    # ------------------------------------------------------

    heat_score = 0
    heat_signals = []

    if temperature >= 32:
        heat_score += 50
        heat_signals.append(
            f"High temperature: {temperature}°C"
        )

    if solar >= 850:
        heat_score += 35
        heat_signals.append(
            f"Extreme solar radiation: {solar} W/m²"
        )

    if wind <= 5:
        heat_score += 15
        heat_signals.append(
            f"Low wind: {wind} m/s"
        )

    if heat_score >= 70:
        return {
            "event": "Heatwave",
            "severity": "High",
            "confidence": min(heat_score, 100),
            "reason": (
                "High temperature combined with strong "
                "solar radiation indicates heatwave conditions."
            ),
            "signals": heat_signals,
        }

    # ------------------------------------------------------
    # HEAVY RAIN
    # ------------------------------------------------------

    rain_score = 0
    rain_signals = []

    if "rain" in weather:
        rain_score += 70
        rain_signals.append(
            "Rain detected"
        )

    if wind >= 8:
        rain_score += 20
        rain_signals.append(
            f"Elevated wind: {wind} m/s"
        )

    if solar < 500:
        rain_score += 10
        rain_signals.append(
            "Low solar radiation"
        )

    if rain_score >= 70:
        return {
            "event": "Heavy Rain",
            "severity": "Moderate",
            "confidence": min(rain_score, 100),
            "reason": (
                "Rain and reduced environmental energy "
                "conditions indicate heavy rainfall."
            ),
            "signals": rain_signals,
        }

    # ------------------------------------------------------
    # HIGH WIND
    # ------------------------------------------------------

    if wind >= 12:
        return {
            "event": "High Wind",
            "severity": "Moderate",
            "confidence": 85,
            "reason": (
                f"Wind speed has reached {wind} m/s, "
                "creating potentially hazardous conditions."
            ),
            "signals": [
                f"Wind speed: {wind} m/s"
            ],
        }

    # ------------------------------------------------------
    # EXTREME SOLAR
    # ------------------------------------------------------

    if solar >= 900:
        return {
            "event": "Extreme Solar",
            "severity": "Moderate",
            "confidence": 90,
            "reason": (
                f"Solar radiation has reached {solar} W/m²."
            ),
            "signals": [
                f"Solar radiation: {solar} W/m²"
            ],
        }

    # ------------------------------------------------------
    # NORMAL
    # ------------------------------------------------------

    return {
        "event": "Normal",
        "severity": "Low",
        "confidence": 98,
        "reason": (
            "No significant environmental threat "
            "was detected."
        ),
        "signals": [],
    }


# ==========================================================
# RESOURCE PRIORITY
# ==========================================================

def build_decision(environment, resources):

    energy = energy_potential(environment)

    event = detect_event(environment)

    # ------------------------------------------------------
    # Event-specific priority adjustments
    # ------------------------------------------------------

    event_priority_boosts = {

        "Storm": {
            "shelter": 6,
            "water": 4,
            "food": 3,
            "fuel": 2,
            "supplies": 2,
            "medical": 4,
        },

        "Heatwave": {
            "water": 6,
            "shelter": 4,
            "food": 2,
            "medical": 3,
        },

        "Heavy Rain": {
            "shelter": 4,
            "water": 2,
            "food": 2,
            "fuel": 1,
            "supplies": 2,
        },

        "High Wind": {
            "shelter": 4,
            "fuel": 2,
            "supplies": 2,
        },

        "Extreme Solar": {
            "water": 3,
            "shelter": 2,
        },
    }

    boosts = event_priority_boosts.get(
        event["event"],
        {},
    )

    # ------------------------------------------------------
    # Rank resources
    # ------------------------------------------------------

    ranked = []

    for resource in resources:

        quantity = max(
            float(resource["quantity"]),
            0,
        )

        # Scarcity increases importance as supplies decrease.
        scarcity = 1 / max(quantity, 1)

        base_score = (
            resource["priority"]
            * (1 + min(scarcity * 100, 1.5))
        )

        resource_name = (
            resource["name"].lower()
        )

        # --------------------------------------------------
        # Find event-related priority boost
        # --------------------------------------------------

        event_boost = 0

        for keyword, boost in boosts.items():

            if keyword in resource_name:
                event_boost = boost
                break

        score = base_score + event_boost

        # --------------------------------------------------
        # Heat increases water importance
        # --------------------------------------------------

        if (
            "water" in resource_name
            and environment["temperature"] >= 27
        ):
            score += 3

        ranked.append(
            {
                **resource,
                "score": round(score, 2),
                "base_score": round(base_score, 2),
                "event_boost": event_boost,
            }
        )

    ranked.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    # ------------------------------------------------------
    # Energy allocation
    # ------------------------------------------------------

    allocations = allocate_energy(
        environment,
        resources,
        energy,
        event,
    )

    # ------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------

    actions = []

    # ------------------------------------------------------
    # Environmental alert
    # ------------------------------------------------------

    if event["event"] != "Normal":

        actions.append(
            {
                "title": (
                    f"⚠️ {event['event']} detected"
                ),

                "detail": (
                    f"{event['reason']} "
                    f"Detection confidence: "
                    f"{event['confidence']}%."
                ),

                "type": "alert",
            }
        )

        if event["signals"]:

            actions.append(
                {
                    "title": "Environmental signals analyzed",

                    "detail": (
                        " • ".join(
                            event["signals"]
                        )
                    ),

                    "type": "detection",
                }
            )

    # ------------------------------------------------------
    # Event-specific actions
    # ------------------------------------------------------

    if event["event"] == "Storm":

        actions.append(
            {
                "title": "Prioritize shelter operations",

                "detail": (
                    "Storm conditions increase the need "
                    "for protected shelter, emergency "
                    "supplies, water, food, and backup fuel."
                ),

                "type": "emergency",
            }
        )

        actions.append(
            {
                "title": "Preserve emergency resources",

                "detail": (
                    "Reduce nonessential usage and reserve "
                    "fuel, food, water, and medical supplies "
                    "for critical operations."
                ),

                "type": "conservation",
            }
        )

    elif event["event"] == "Heatwave":

        actions.append(
            {
                "title": "Increase water priority",

                "detail": (
                    "High temperature and solar radiation "
                    "increase water demand and cooling needs."
                ),

                "type": "emergency",
            }
        )

        actions.append(
            {
                "title": "Protect cooling and shelter capacity",

                "detail": (
                    "Reserve energy for cooling centers, "
                    "medical facilities, and vulnerable "
                    "residents."
                ),

                "type": "energy",
            }
        )

    elif event["event"] == "Heavy Rain":

        actions.append(
            {
                "title": "Prepare shelters and drainage",

                "detail": (
                    "Heavy rainfall increases the risk "
                    "of flooding and infrastructure disruption."
                ),

                "type": "emergency",
            }
        )

    elif event["event"] == "High Wind":

        actions.append(
            {
                "title": "Secure exposed infrastructure",

                "detail": (
                    "High winds increase the risk of "
                    "damage to exposed equipment and buildings."
                ),

                "type": "emergency",
            }
        )

    elif event["event"] == "Extreme Solar":

        actions.append(
            {
                "title": "Use excess solar strategically",

                "detail": (
                    "Strong solar generation creates an "
                    "opportunity to charge storage and "
                    "operate flexible loads."
                ),

                "type": "energy",
            }
        )

    # ------------------------------------------------------
    # Top resource
    # ------------------------------------------------------

    if ranked:

        top = ranked[0]

        actions.append(
            {
                "title": (
                    f"Prioritize "
                    f"{top['name'].lower()} operations"
                ),

                "detail": (
                    f"Current decision score: "
                    f"{top['score']}. "
                    f"Base priority: "
                    f"{top['priority']}/10. "
                    f"{top['quantity']} "
                    f"{top['unit']} available."
                ),

                "type": "priority",
            }
        )

    # ------------------------------------------------------
    # Energy recommendations
    # ------------------------------------------------------

    if energy["solar_level"] == "High":

        actions.append(
            {
                "title": "Run high-load tasks on solar",

                "detail": (
                    "Strong sunlight makes desalination, "
                    "charging, and pumping good uses "
                    "of current renewable generation."
                ),

                "type": "energy",
            }
        )

    elif energy["wind_level"] == "High":

        actions.append(
            {
                "title": "Use wind generation first",

                "detail": (
                    "Wind is currently a strong renewable "
                    "source. Reserve fuel for critical backup."
                ),

                "type": "energy",
            }
        )

    else:

        actions.append(
            {
                "title": "Conserve and store energy",

                "detail": (
                    "Renewable output is moderate or low, "
                    "so defer flexible loads and protect "
                    "the battery reserve."
                ),

                "type": "energy",
            }
        )

    # ------------------------------------------------------
    # Storage
    # ------------------------------------------------------

    actions.append(
        {
            "title": "Store remaining energy",

            "detail": (
                "Keep surplus energy in storage for "
                "future low-production periods and "
                "overnight demand."
            ),

            "type": "storage",
        }
    )

    # ------------------------------------------------------
    # Final decision
    # ------------------------------------------------------

    return {
        "environment": environment,
        "energy": energy,
        "energy_allocation": allocations,
        "event": event,
        "resources": ranked,
        "recommendations": actions,
    }


# ==========================================================
# AUTOMATIC ENERGY ALLOCATION
# ==========================================================

def allocate_energy(
    environment,
    resources,
    energy,
    event=None,
):
    """
    Automatically determines how renewable energy
    should be distributed across island systems.

    Event detection changes the allocation strategy.
    """

    total_kw = energy["total_kw"]

    # ------------------------------------------------------
    # Base allocation
    # ------------------------------------------------------

    allocations = {
        "💧 Water / Desalination": 30,
        "🏥 Emergency Systems": 25,
        "🏠 Essential Housing": 25,
        "🔋 Battery Storage": 20,
    }

    # ------------------------------------------------------
    # Water scarcity
    # ------------------------------------------------------

    water = next(
        (
            resource
            for resource in resources
            if "water" in resource["name"].lower()
        ),
        None,
    )

    if water and water["quantity"] < 500:

        allocations[
            "💧 Water / Desalination"
        ] += 20

        allocations[
            "🔋 Battery Storage"
        ] -= 10

        allocations[
            "🏠 Essential Housing"
        ] -= 10

    # ------------------------------------------------------
    # High temperature
    # ------------------------------------------------------

    if environment["temperature"] >= 28:

        allocations[
            "🏠 Essential Housing"
        ] += 10

        allocations[
            "🔋 Battery Storage"
        ] -= 10

    # ------------------------------------------------------
    # Cloudy conditions
    # ------------------------------------------------------

    if environment["weather"] == "Cloudy":

        allocations[
            "🔋 Battery Storage"
        ] += 10

        allocations[
            "🏠 Essential Housing"
        ] -= 5

        allocations[
            "💧 Water / Desalination"
        ] -= 5

    # ------------------------------------------------------
    # STORM RESPONSE
    # ------------------------------------------------------

    if event and event["event"] == "Storm":

        allocations[
            "🏥 Emergency Systems"
        ] += 15

        allocations[
            "🏠 Essential Housing"
        ] += 15

        allocations[
            "🔋 Battery Storage"
        ] += 10

        allocations[
            "💧 Water / Desalination"
        ] -= 20

    # ------------------------------------------------------
    # HEATWAVE RESPONSE
    # ------------------------------------------------------

    elif event and event["event"] == "Heatwave":

        allocations[
            "💧 Water / Desalination"
        ] += 20

        allocations[
            "🏠 Essential Housing"
        ] += 15

        allocations[
            "🔋 Battery Storage"
        ] -= 20

        allocations[
            "🏥 Emergency Systems"
        ] -= 15

    # ------------------------------------------------------
    # HIGH WIND RESPONSE
    # ------------------------------------------------------

    elif event and event["event"] == "High Wind":

        allocations[
            "🏥 Emergency Systems"
        ] += 10

        allocations[
            "🏠 Essential Housing"
        ] += 10

        allocations[
            "🔋 Battery Storage"
        ] += 10

        allocations[
            "💧 Water / Desalination"
        ] -= 10

    # ------------------------------------------------------
    # Heavy rain response
    # ------------------------------------------------------

    elif event and event["event"] == "Heavy Rain":

        allocations[
            "🏠 Essential Housing"
        ] += 10

        allocations[
            "🏥 Emergency Systems"
        ] += 10

        allocations[
            "🔋 Battery Storage"
        ] += 10

        allocations[
            "💧 Water / Desalination"
        ] -= 10

    # ------------------------------------------------------
    # Extreme solar response
    # ------------------------------------------------------

    elif event and event["event"] == "Extreme Solar":

        allocations[
            "💧 Water / Desalination"
        ] += 10

        allocations[
            "🔋 Battery Storage"
        ] += 10

        allocations[
            "🏠 Essential Housing"
        ] -= 10

        allocations[
            "🏥 Emergency Systems"
        ] -= 10

    # ------------------------------------------------------
    # Prevent negative allocations
    # ------------------------------------------------------

    for system in allocations:

        allocations[system] = max(
            0,
            allocations[system],
        )

    # ------------------------------------------------------
    # Normalize allocations to 100%
    # ------------------------------------------------------

    total_percent = sum(
        allocations.values()
    )

    if total_percent <= 0:
        total_percent = 1

    results = []

    for system, percent in allocations.items():

        normalized_percent = (
            percent
            / total_percent
            * 100
        )

        results.append(
            {
                "system": system,
                "percent": round(
                    normalized_percent,
                    1,
                ),
                "kw": round(
                    total_kw
                    * normalized_percent
                    / 100,
                    2,
                ),
            }
        )

    return results