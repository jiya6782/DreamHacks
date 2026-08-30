"""Decision engine for island energy and resource management."""

import re
from typing import Any, Dict, List, Optional


SEVERITY_RANK = {
    "Normal": 1,
    "Moderate": 2,
    "High": 3,
    "Critical": 4,
}


# --------------------------------------------------
# ENERGY CALCULATION
# --------------------------------------------------

def energy_potential(environment: Dict[str, Any]) -> Dict[str, Any]:
    """Estimate renewable energy available from solar and wind."""

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


# --------------------------------------------------
# ENVIRONMENTAL EVENT DETECTION (primary / unchanged)
# --------------------------------------------------

def detect_environmental_event(
    environment: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Analyze sensor data and determine whether a significant
    environmental condition or disaster is occurring.

    This returns the single highest-priority *environmental*
    (weather/sensor) event. Resource-driven conditions (e.g. a
    water shortage) are layered on separately in
    `detect_resource_conditions` and combined in `build_decision`
    so this function's behavior/contract stays stable.
    """

    temperature = float(environment.get("temperature", 0))
    solar = float(environment.get("solar_radiation", 0))
    wind = float(environment.get("wind_speed", 0))
    rainfall = float(environment.get("rainfall", 0))
    weather = str(environment.get("weather", "")).lower()

    # ----------------------------------------------
    # STORM
    # ----------------------------------------------

    if (
        rainfall >= 5
        and wind >= 12
    ) or (
        weather == "storm"
    ):
        return {
            "event": "Storm",
            "severity": "Critical",
            "icon": "🌪️",
            "description": (
                "Heavy rainfall and high winds indicate "
                "a storm is affecting the island."
            ),
            "reason": (
                f"Rainfall: {rainfall} mm/h + "
                f"Wind: {wind} m/s"
            ),
        }

    # ----------------------------------------------
    # HEATWAVE
    # ----------------------------------------------

    if (
        temperature >= 29
        and solar >= 800
    ):
        return {
            "event": "Heatwave",
            "severity": "High",
            "icon": "🔥",
            "description": (
                "Extreme heat combined with intense solar "
                "radiation indicates a heatwave."
            ),
            "reason": (
                f"Temperature: {temperature}°C + "
                f"Solar radiation: {solar} W/m²"
            ),
        }

    # ----------------------------------------------
    # HEAVY RAIN
    # ----------------------------------------------

    if rainfall >= 8:
        return {
            "event": "Heavy Rain",
            "severity": "Moderate",
            "icon": "🌧️",
            "description": (
                "Heavy rainfall has been detected. "
                "Water collection can be prioritized."
            ),
            "reason": f"Rainfall: {rainfall} mm/h",
        }

    # ----------------------------------------------
    # HIGH WIND
    # ----------------------------------------------

    if wind >= 15:
        return {
            "event": "High Wind",
            "severity": "Moderate",
            "icon": "🌬️",
            "description": (
                "Strong winds may require protection "
                "of infrastructure and equipment."
            ),
            "reason": f"Wind speed: {wind} m/s",
        }

    # ----------------------------------------------
    # HIGH SOLAR
    # ----------------------------------------------

    if solar >= 900:
        return {
            "event": "Extreme Solar",
            "severity": "Moderate",
            "icon": "☀️",
            "description": (
                "Very high solar radiation creates "
                "increased cooling and water demand."
            ),
            "reason": f"Solar radiation: {solar} W/m²",
        }

    # ----------------------------------------------
    # NORMAL
    # ----------------------------------------------

    return {
        "event": "Normal Conditions",
        "severity": "Normal",
        "icon": "🟢",
        "description": (
            "No significant environmental threat "
            "has been detected."
        ),
        "reason": "All monitored conditions are within normal ranges.",
    }


# --------------------------------------------------
# RESOURCE-DRIVEN CONDITIONS (compounding layer)
# --------------------------------------------------

def detect_resource_conditions(
    resources: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Detect shortages driven by the resource ledger itself, independent
    of weather. These can *stack* with an environmental event (e.g. a
    Storm arriving during an existing Water Shortage is materially
    worse than either condition alone), which a simple if/elif chain
    over a single "event" can't represent.
    """

    conditions = []

    for resource in resources:

        name = str(resource.get("name", "")).lower()
        category = str(resource.get("category", "")).lower()
        quantity = max(float(resource.get("quantity", 0)), 0)
        unit = resource.get("unit", "")

        if ("water" in name or category == "water") and quantity < 500:
            conditions.append({
                "name": "Water Shortage",
                "icon": "💧",
                "severity": "High",
                "resource": resource["name"],
                "detail": (
                    f"{resource['name']} at {quantity} {unit} is "
                    f"below the 500-{unit or 'unit'} safety threshold."
                ),
            })

        elif ("fuel" in name or category == "fuel") and quantity < 150:
            conditions.append({
                "name": "Fuel Shortage",
                "icon": "⛽",
                "severity": "Moderate",
                "resource": resource["name"],
                "detail": (
                    f"{resource['name']} at {quantity} {unit} is "
                    "running low."
                ),
            })

        elif (
            "shelter" in name or "housing" in name
        ) and quantity < 15:
            conditions.append({
                "name": "Shelter Shortage",
                "icon": "🏠",
                "severity": "High",
                "resource": resource["name"],
                "detail": (
                    f"{resource['name']} capacity ({quantity} {unit}) "
                    "may not cover the population if conditions worsen."
                ),
            })

        elif ("food" in name or category == "food") and quantity < 150:
            conditions.append({
                "name": "Food Shortage",
                "icon": "🍽️",
                "severity": "Moderate",
                "resource": resource["name"],
                "detail": (
                    f"{resource['name']} at {quantity} {unit} is "
                    "running low."
                ),
            })

    return conditions


def combine_event(
    primary_event: Dict[str, Any],
    resource_conditions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Merge the primary environmental event with any active resource
    conditions into a single display-ready picture, without mutating
    the original `event`/`severity` fields that existing callers and
    tests rely on.
    """

    combined = dict(primary_event)

    combined_severity = primary_event["severity"]
    for condition in resource_conditions:
        if SEVERITY_RANK[condition["severity"]] > SEVERITY_RANK[combined_severity]:
            combined_severity = condition["severity"]

    title_parts = [f"{primary_event['icon']} {primary_event['event']}"]
    title_parts += [
        f"{c['icon']} {c['name']}" for c in resource_conditions
    ]

    combined["compound_conditions"] = resource_conditions
    combined["combined_severity"] = combined_severity
    combined["display_title"] = " + ".join(title_parts)
    combined["is_compound"] = len(resource_conditions) > 0

    return combined


# --------------------------------------------------
# PREDICTIVE DEPLETION FORECAST
# --------------------------------------------------

def estimate_hours_remaining(resource: Dict[str, Any]) -> Optional[float]:
    """
    Turn a resource's stated `horizon` (e.g. "4.0 days", "18 hours")
    into hours-remaining, if the ledger provides one. Returns None
    when no horizon is available so callers can skip forecasting
    for resources that don't track it.
    """

    horizon = resource.get("horizon")

    if not horizon:
        return None

    match = re.match(
        r"\s*([\d.]+)\s*(day|hour|hr)",
        str(horizon).lower(),
    )

    if not match:
        return None

    value = float(match.group(1))
    unit = match.group(2)

    return value * 24 if unit == "day" else value


def forecast_resource(resource: Dict[str, Any]) -> Dict[str, Any]:
    """Build a small predictive summary for one resource."""

    hours_remaining = estimate_hours_remaining(resource)

    if hours_remaining is None:
        return {"hours_remaining": None, "urgency": "Unknown", "urgency_bonus": 0}

    if hours_remaining < 24:
        urgency, bonus = "Critical", 4
    elif hours_remaining < 72:
        urgency, bonus = "Elevated", 2
    elif hours_remaining < 168:
        urgency, bonus = "Watch", 1
    else:
        urgency, bonus = "Stable", 0

    return {
        "hours_remaining": hours_remaining,
        "urgency": urgency,
        "urgency_bonus": bonus,
    }


# --------------------------------------------------
# RESOURCE SCORING
# --------------------------------------------------

def build_decision(environment, resources):

    energy = energy_potential(environment)

    primary_event = detect_environmental_event(environment)
    resource_conditions = detect_resource_conditions(resources)
    event = combine_event(primary_event, resource_conditions)

    shortage_resource_names = {
        c["resource"] for c in resource_conditions
    }

    # ----------------------------------------------
    # RESOURCE RANKING
    # ----------------------------------------------

    ranked = []

    for resource in resources:

        quantity = max(
            float(resource["quantity"]),
            0,
        )

        priority = int(resource["priority"])

        scarcity = 1 / max(quantity, 1)

        base_score = priority
        scarcity_bonus = round(
            priority * min(scarcity * 100, 1.5),
            2,
        )

        name = resource["name"].lower()
        category = resource.get(
            "category",
            "",
        ).lower()

        heat_bonus = 0
        event_bonus = 0
        shortage_bonus = 0

        # ------------------------------------------
        # WATER + HEAT
        # ------------------------------------------

        if (
            ("water" in name or category == "water")
            and environment["temperature"] >= 27
        ):
            heat_bonus += 3

        # ------------------------------------------
        # EVENT-SPECIFIC PRIORITIES
        # ------------------------------------------

        if primary_event["event"] == "Storm":

            if (
                "shelter" in name
                or "housing" in name
                or category == "general"
            ):
                event_bonus += 8

            if "fuel" in name:
                event_bonus += 5

            if "water" in name:
                event_bonus += 3

        elif primary_event["event"] == "Heatwave":

            if "water" in name:
                event_bonus += 8

            if "food" in name:
                event_bonus += 2

        elif primary_event["event"] == "Heavy Rain":

            if "water" in name:
                event_bonus += 4

        elif primary_event["event"] == "High Wind":

            if (
                "shelter" in name
                or "housing" in name
                or category == "general"
            ):
                event_bonus += 5

            if "fuel" in name:
                event_bonus += 3

        elif primary_event["event"] == "Extreme Solar":

            if "water" in name:
                event_bonus += 4

        # ------------------------------------------
        # RESOURCE-DRIVEN SHORTAGE BUMP
        # ------------------------------------------

        if resource["name"] in shortage_resource_names:
            shortage_bonus += 3

        # ------------------------------------------
        # PREDICTIVE DEPLETION FORECAST
        # ------------------------------------------

        forecast = forecast_resource(resource)
        urgency_bonus = forecast["urgency_bonus"]

        score = round(
            base_score
            + scarcity_bonus
            + heat_bonus
            + event_bonus
            + shortage_bonus
            + urgency_bonus,
            2,
        )

        ranked.append(
            {
                **resource,
                "score": score,
                "forecast": forecast,
                "breakdown": {
                    "base_priority": base_score,
                    "scarcity_bonus": scarcity_bonus,
                    "heat_bonus": heat_bonus,
                    "event_bonus": event_bonus,
                    "shortage_bonus": shortage_bonus,
                    "urgency_bonus": urgency_bonus,
                    "total": score,
                },
            }
        )

    ranked.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    # ----------------------------------------------
    # PRIMARY RECOMMENDATION
    # ----------------------------------------------

    if ranked:

        top = ranked[0]

        actions = [
            {
                "title": (
                    f"Prioritize "
                    f"{top['name'].lower()} operations"
                ),
                "detail": (
                    f"Priority {top['priority']}/10 leads "
                    f"the current ranking, with "
                    f"{top['quantity']} {top['unit']} available."
                ),
                "type": "priority",
            }
        ]

    else:

        actions = [
            {
                "title": "No resources available",
                "detail": (
                    "The resource ledger is empty. "
                    "Add resources to activate prioritization."
                ),
                "type": "priority",
            }
        ]

    # ----------------------------------------------
    # DISASTER RESPONSE
    # ----------------------------------------------

    if primary_event["event"] == "Storm":

        actions.insert(
            0,
            {
                "title": "🚨 Activate storm response",
                "detail": (
                    "High winds and rainfall indicate a storm. "
                    "Protect shelter, emergency systems, and "
                    "critical infrastructure before flexible loads."
                ),
                "type": "emergency",
            },
        )

    elif primary_event["event"] == "Heatwave":

        actions.insert(
            0,
            {
                "title": "🔥 Activate heatwave response",
                "detail": (
                    "Extreme heat and solar radiation detected. "
                    "Increase water availability, cooling, and "
                    "hydration support."
                ),
                "type": "emergency",
            },
        )

    elif primary_event["event"] == "Heavy Rain":

        actions.insert(
            0,
            {
                "title": "🌧️ Prepare for heavy rainfall",
                "detail": (
                    "Rainfall is elevated. Capture available "
                    "rainwater while protecting vulnerable supplies."
                ),
                "type": "warning",
            },
        )

    elif primary_event["event"] == "High Wind":

        actions.insert(
            0,
            {
                "title": "🌬️ Protect infrastructure",
                "detail": (
                    "Strong winds detected. Secure exposed "
                    "equipment and reduce non-essential loads."
                ),
                "type": "warning",
            },
        )

    elif primary_event["event"] == "Extreme Solar":

        actions.insert(
            0,
            {
                "title": "☀️ Manage extreme solar exposure",
                "detail": (
                    "Solar radiation is unusually high. "
                    "Use renewable generation while prioritizing "
                    "cooling and water systems."
                ),
                "type": "warning",
            },
        )

    # ----------------------------------------------
    # COMPOUND CONDITION CALLOUTS
    # ----------------------------------------------

    for condition in resource_conditions:

        actions.insert(
            1 if primary_event["event"] != "Normal Conditions" else 0,
            {
                "title": (
                    f"{condition['icon']} {condition['name']}"
                    + (
                        f" during {primary_event['event']}"
                        if primary_event["event"] != "Normal Conditions"
                        else ""
                    )
                ),
                "detail": condition["detail"] + (
                    " This is compounding with the active environmental "
                    "event above — treat it as a combined emergency, "
                    "not two separate issues."
                    if primary_event["event"] != "Normal Conditions"
                    else ""
                ),
                "type": "emergency" if condition["severity"] in ("Critical", "High") else "warning",
            },
        )

    # ----------------------------------------------
    # PREDICTIVE DEPLETION WARNINGS
    # ----------------------------------------------

    for item in ranked:

        forecast = item["forecast"]

        if forecast["hours_remaining"] is not None and forecast["hours_remaining"] < 72:

            hours = forecast["hours_remaining"]

            display_time = (
                f"{hours:.0f} hours"
                if hours < 48
                else f"{hours / 24:.1f} days"
            )

            actions.append(
                {
                    "title": f"⏳ {item['name']} projected to run out in {display_time}",
                    "detail": (
                        f"At current consumption, {item['name'].lower()} "
                        f"has roughly {display_time} of supply left "
                        f"({forecast['urgency']} urgency). Increase "
                        "production, rationing, or resupply now rather "
                        "than after it's critical."
                    ),
                    "type": "forecast",
                }
            )

    # ----------------------------------------------
    # ENERGY RESPONSE
    # ----------------------------------------------

    if energy["solar_level"] == "High":

        actions.append(
            {
                "title": "Run high-load tasks on solar",
                "detail": (
                    "Strong sunlight makes desalination, "
                    "charging, and pumping good uses of "
                    "current renewable generation."
                ),
                "type": "energy",
            }
        )

    elif energy["wind_level"] == "High":

        actions.append(
            {
                "title": "Use wind generation first",
                "detail": (
                    "Wind is the strongest renewable source "
                    "right now. Reserve fuel for critical backup."
                ),
                "type": "energy",
            }
        )

    else:

        actions.append(
            {
                "title": "Conserve and store energy",
                "detail": (
                    "Renewable output is moderate or low. "
                    "Defer flexible loads and protect the "
                    "battery reserve."
                ),
                "type": "energy",
            }
        )

    # ----------------------------------------------
    # STORAGE
    # ----------------------------------------------

    if primary_event["event"] in [
        "Storm",
        "High Wind",
        "Heatwave",
    ]:

        actions.append(
            {
                "title": "Increase emergency battery reserve",
                "detail": (
                    "Environmental risk is elevated. "
                    "Reserve renewable energy for critical "
                    "systems if conditions worsen."
                ),
                "type": "storage",
            }
        )

    else:

        actions.append(
            {
                "title": "Store remaining energy",
                "detail": (
                    "Keep surplus energy in storage for the "
                    "next low-production period and overnight demand."
                ),
                "type": "storage",
            }
        )

    energy_allocation = allocate_energy(environment, resources, energy)

    return {
        "environment": environment,
        "energy": energy,
        "event": event,
        "resources": ranked,
        "recommendations": actions,
        "energy_allocation": energy_allocation,
    }


# --------------------------------------------------
# AUTOMATIC ENERGY ALLOCATION
# --------------------------------------------------

def allocate_energy(environment, resources, energy):

    """
    Automatically decides how available renewable energy
    should be distributed across island operations.
    """

    total_kw = energy["total_kw"]

    water = next(
        (
            resource
            for resource in resources
            if "water" in resource["name"].lower()
        ),
        None,
    )

    allocations = {
        "💧 Water / Desalination": 30,
        "🏥 Emergency Systems": 25,
        "🏠 Essential Housing": 25,
        "🔋 Battery Storage": 20,
    }

    event = detect_environmental_event(environment)

    # ----------------------------------------------
    # WATER SHORTAGE
    # ----------------------------------------------

    if water and water["quantity"] < 500:

        allocations["💧 Water / Desalination"] += 20
        allocations["🔋 Battery Storage"] -= 10
        allocations["🏠 Essential Housing"] -= 10

    # ----------------------------------------------
    # HIGH TEMPERATURE
    # ----------------------------------------------

    if environment["temperature"] >= 28:

        allocations["🏠 Essential Housing"] += 10
        allocations["🔋 Battery Storage"] -= 10

    # ----------------------------------------------
    # STORM
    # ----------------------------------------------

    if event["event"] == "Storm":

        allocations["🏥 Emergency Systems"] += 15
        allocations["🏠 Essential Housing"] += 20
        allocations["🔋 Battery Storage"] += 15
        allocations["💧 Water / Desalination"] -= 10

    # ----------------------------------------------
    # HEATWAVE
    # ----------------------------------------------

    if event["event"] == "Heatwave":

        allocations["💧 Water / Desalination"] += 20
        allocations["🏠 Essential Housing"] += 10
        allocations["🔋 Battery Storage"] -= 10

    # ----------------------------------------------
    # HIGH WIND
    # ----------------------------------------------

    if event["event"] == "High Wind":

        allocations["🏠 Essential Housing"] += 10
        allocations["🏥 Emergency Systems"] += 10
        allocations["🔋 Battery Storage"] += 10

    # ----------------------------------------------
    # CLOUDY CONDITIONS
    # ----------------------------------------------

    if environment["weather"] == "Cloudy":

        allocations["🔋 Battery Storage"] += 10
        allocations["🏠 Essential Housing"] -= 5
        allocations["💧 Water / Desalination"] -= 5

    # ----------------------------------------------
    # PREVENT NEGATIVE VALUES
    # ----------------------------------------------

    for system in allocations:

        allocations[system] = max(
            0,
            allocations[system],
        )

    # ----------------------------------------------
    # NORMALIZE TO 100%
    # ----------------------------------------------

    total_percent = sum(
        allocations.values()
    )

    if total_percent > 0:

        allocations = {
            system: round(
                percent / total_percent * 100,
                1,
            )
            for system, percent in allocations.items()
        }

    # ----------------------------------------------
    # CALCULATE kW
    # ----------------------------------------------

    results = []

    for system, percent in allocations.items():

        results.append(
            {
                "system": system,
                "percent": percent,
                "kw": round(
                    total_kw * percent / 100,
                    2,
                ),
            }
        )

    return results