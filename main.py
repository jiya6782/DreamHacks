import copy

import streamlit as st

from decision_engine import build_decision
from environmental_simulator import EnvironmentalSimulator
from resource_manager import ResourceManager


# --------------------------------------------------
# APP CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Island Resource Dashboard",
    page_icon="🌱",
    layout="wide",
)


# --------------------------------------------------
# CUSTOM STYLING
# --------------------------------------------------

st.markdown(
    """
    <style>

    .event-critical {
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #dc6d57;
        background-color: #fff0ec;
    }

    .event-high {
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #e6a23c;
        background-color: #fff8e8;
    }

    .event-normal {
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #b8e0cf;
        background-color: #effaf5;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# SIMULATION
# --------------------------------------------------

@st.cache_resource
def get_simulator():
    return EnvironmentalSimulator()


simulator = get_simulator()


# --------------------------------------------------
# RESOURCE MANAGER
# --------------------------------------------------

resource_manager = ResourceManager()


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("🌱 Island Resource Command Center")

st.caption(
    "Autonomous environmental monitoring and "
    "resource allocation system"
)


# --------------------------------------------------
# CONTROLS
# --------------------------------------------------

col1, col2 = st.columns([1, 4])

with col1:

    if st.button(
        "🔄 Advance Simulation",
        use_container_width=True,
    ):

        simulator.advance()

        st.rerun()


# --------------------------------------------------
# DEMO MODE — manually inject conditions live
# --------------------------------------------------

st.sidebar.header("🧪 Demo Mode")

st.sidebar.caption(
    "Override live sensor data to show how the engine reacts, "
    "without waiting for the simulation to reach that step."
)

demo_scenario = st.sidebar.selectbox(
    "Simulate a condition",
    [
        "Live Simulation",
        "Storm",
        "Heatwave",
        "Heavy Rain",
        "High Wind",
        "Extreme Solar",
        "Water Shortage",
        "Storm + Water Shortage (compound)",
    ],
)

DEMO_OVERRIDES = {
    "Storm": {"wind_speed": 20.0, "rainfall": 15.0, "weather": "Storm"},
    "Heatwave": {"temperature": 32.0, "solar_radiation": 950},
    "Heavy Rain": {"rainfall": 9.0, "weather": "Rain"},
    "High Wind": {"wind_speed": 18.0},
    "Extreme Solar": {"solar_radiation": 920},
}


# --------------------------------------------------
# CURRENT DATA
# --------------------------------------------------

environment = simulator.snapshot()
resources = resource_manager.get_all_resources()

# Demo overrides are applied to *copies* so the underlying
# simulator/ledger state is never mutated by exploring a scenario.
demo_environment = dict(environment)
demo_resources = [dict(r) for r in resources]

if demo_scenario in DEMO_OVERRIDES:
    demo_environment.update(DEMO_OVERRIDES[demo_scenario])

if demo_scenario in ("Water Shortage", "Storm + Water Shortage (compound)"):
    for r in demo_resources:
        if "water" in r["name"].lower():
            r["quantity"] = 180.0
            r["horizon"] = "0.8 days"

if demo_scenario == "Storm + Water Shortage (compound)":
    demo_environment.update(DEMO_OVERRIDES["Storm"])

if demo_scenario != "Live Simulation":
    st.warning(
        f"🧪 DEMO MODE ACTIVE — simulating **{demo_scenario}**. "
        "Sensor data below is overridden for demonstration; "
        "select 'Live Simulation' to return to real data.",
        icon="🧪",
    )

decision = build_decision(demo_environment, demo_resources)

energy = decision["energy"]
event = decision["event"]


# --------------------------------------------------
# ENVIRONMENTAL EVENT
# --------------------------------------------------

st.subheader("🚨 Environmental Intelligence")

severity = event["combined_severity"]

if severity == "Critical":

    st.error(event["display_title"] + " — CRITICAL CONDITION")

elif severity == "High":

    st.warning(event["display_title"] + " — HIGH RISK")

elif severity == "Moderate":

    st.warning(event["display_title"] + " — MONITORING")

else:

    st.success(event["display_title"])


event_cols = st.columns(3)

event_cols[0].metric(
    "Detected Condition",
    event["event"],
)

event_cols[1].metric(
    "Severity",
    severity,
)

event_cols[2].metric(
    "Detection Confidence",
    "Rule-based",
)


st.info(
    f"**Why?** {event['description']} "
    f"Sensor evidence: {event['reason']}"
)

if event["is_compound"]:

    st.markdown("**⚡ Compounding conditions detected:**")

    for condition in event["compound_conditions"]:

        st.markdown(
            f"- {condition['icon']} **{condition['name']}** "
            f"({condition['severity']}) — {condition['detail']}"
        )

    st.caption(
        "These resource-driven conditions are stacking with the "
        "environmental event above, rather than being evaluated in "
        "isolation — the response below treats them as one combined "
        "emergency."
    )


# --------------------------------------------------
# SIMULATION STATUS
# --------------------------------------------------

st.subheader("🌎 Live Environmental Data")

cols = st.columns(6)

cols[0].metric(
    "Solar Radiation",
    f"{demo_environment['solar_radiation']} W/m²",
)

cols[1].metric(
    "Wind Speed",
    f"{demo_environment['wind_speed']} m/s",
)

cols[2].metric(
    "Temperature",
    f"{demo_environment['temperature']} °C",
)

cols[3].metric(
    "Rainfall",
    f"{demo_environment['rainfall']} mm/h",
)

cols[4].metric(
    "Weather",
    demo_environment["weather"],
)

cols[5].metric(
    "Time",
    demo_environment.get("time_of_day", "—"),
)


# --------------------------------------------------
# RENEWABLE ENERGY
# --------------------------------------------------

st.subheader("⚡ Renewable Energy Potential")

energy_cols = st.columns(3)

energy_cols[0].metric(
    "☀️ Solar",
    f"{energy['solar_kw']} kW",
    energy["solar_level"],
)

energy_cols[1].metric(
    "🌬️ Wind",
    f"{energy['wind_kw']} kW",
    energy["wind_level"],
)

energy_cols[2].metric(
    "⚡ Total Available",
    f"{energy['total_kw']} kW",
)


# --------------------------------------------------
# AUTOMATIC ENERGY ALLOCATION
# --------------------------------------------------

st.subheader("🔋 Autonomous Energy Allocation")

allocations = decision["energy_allocation"]

for allocation in allocations:

    system = allocation["system"]

    percent = allocation["percent"]

    kw = allocation["kw"]

    st.write(
        f"**{system}** — "
        f"{percent}%  |  {kw} kW"
    )

    st.progress(
        min(
            int(percent),
            100,
        )
    )


# --------------------------------------------------
# RESOURCE LEDGER
# --------------------------------------------------

resource_manager.show_resource_ledger()


# --------------------------------------------------
# AI RESOURCE RANKING
# --------------------------------------------------

st.subheader("🧠 Adaptive Resource Priorities")

st.caption(
    "Expand a resource to see exactly how its score was built — "
    "base priority, scarcity, event effects, and depletion urgency."
)

for i, resource in enumerate(
    decision["resources"],
    start=1,
):

    col1, col2, col3, col4 = st.columns(
        [0.5, 3, 1, 1]
    )

    with col1:

        st.markdown(
            f"### {i}"
        )

    with col2:

        st.markdown(
            f"**{resource['name']}**"
        )

        st.caption(
            f"{resource['quantity']} "
            f"{resource['unit']}"
        )

    with col3:

        st.write(
            f"Priority: {resource['priority']}/10"
        )

    with col4:

        st.write(
            f"Score: {resource['score']}"
        )

    breakdown = resource["breakdown"]
    forecast = resource["forecast"]

    with st.expander(f"Why is {resource['name']} ranked #{i}?"):

        st.write(f"**Base priority:** {breakdown['base_priority']}")
        st.write(
            f"**Scarcity bonus:** +{breakdown['scarcity_bonus']} "
            "(lower quantity → higher bonus)"
        )
        st.write(f"**Heat/water bonus:** +{breakdown['heat_bonus']}")
        st.write(
            f"**Active event bonus:** +{breakdown['event_bonus']} "
            f"(from {event['event']})"
        )
        st.write(
            f"**Shortage bonus:** +{breakdown['shortage_bonus']} "
            "(resource-driven condition active)"
        )
        st.write(
            f"**Depletion urgency bonus:** +{breakdown['urgency_bonus']} "
            f"({forecast['urgency']})"
        )
        st.markdown(f"**Total score: {breakdown['total']}**")

        if forecast["hours_remaining"] is not None:
            st.caption(
                f"Projected to deplete in "
                f"{forecast['hours_remaining']:.0f} hours at current "
                "consumption."
            )


# --------------------------------------------------
# RECOMMENDED ACTIONS
# --------------------------------------------------

st.subheader(
    "🤖 Recommended Next Actions"
)

for i, recommendation in enumerate(
    decision["recommendations"],
    start=1,
):

    recommendation_type = recommendation["type"]

    if recommendation_type == "emergency":

        st.error(
            f"### 🚨 {i}. "
            f"{recommendation['title']}"
        )

    elif recommendation_type == "warning":

        st.warning(
            f"### ⚠️ {i}. "
            f"{recommendation['title']}"
        )

    elif recommendation_type == "forecast":

        st.info(
            f"### ⏳ {i}. "
            f"{recommendation['title']}"
        )

    else:

        st.markdown(
            f"### {i}. "
            f"{recommendation['title']}"
        )

    st.write(
        recommendation["detail"]
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "SIMULATION MODE / ENVIRONMENTAL SENSORS ACTIVE"
)

st.caption(
    "Decision Engine v3.0 — Compound-Aware, Predictive Disaster Response"
)