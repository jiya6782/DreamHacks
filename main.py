import streamlit as st

from decision_engine import build_decision
from environmental_simulator import EnvironmentalSimulator
from resource_manager import ResourceManager


# ==========================================================
# APP CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="Island Resource Dashboard",
    page_icon="🌱",
    layout="wide",
)


# ==========================================================
# SIMULATION STATE
# ==========================================================

@st.cache_resource
def get_simulator():
    return EnvironmentalSimulator()


simulator = get_simulator()


# ==========================================================
# RESOURCE MANAGER
# ==========================================================

resource_manager = ResourceManager()


# ==========================================================
# HEADER
# ==========================================================

st.title("🌱 Island Resource Dashboard")

st.caption(
    "Simulation-first environmental resource management"
)


# ==========================================================
# CONTROLS
# ==========================================================

col1, col2 = st.columns([1, 4])

with col1:

    if st.button(
        "🔄 Advance Simulation",
        use_container_width=True,
    ):

        simulator.advance()

        st.rerun()


# ==========================================================
# GET CURRENT DATA
# ==========================================================

environment = simulator.snapshot()

resources = resource_manager.get_all_resources()

decision = build_decision(
    environment,
    resources,
)


# ==========================================================
# SIMULATION STATUS
# ==========================================================

st.subheader("Simulation Status")

cols = st.columns(5)

cols[0].metric(
    "Solar Radiation",
    f"{environment['solar_radiation']} W/m²",
)

cols[1].metric(
    "Wind Speed",
    f"{environment['wind_speed']} m/s",
)

cols[2].metric(
    "Temperature",
    f"{environment['temperature']} °C",
)

cols[3].metric(
    "Weather",
    environment["weather"],
)

cols[4].metric(
    "Time",
    environment["time_of_day"],
)


# ==========================================================
# ENVIRONMENTAL EVENT DETECTION
# ==========================================================

st.subheader("🌎 Environmental Assessment")

event = decision["event"]


if event["event"] == "Normal":

    st.success(
        f"🟢 NORMAL CONDITIONS\n\n"
        f"{event['reason']}"
    )

else:

    if event["severity"] == "High":

        st.error(
            f"🔴 {event['event'].upper()} DETECTED"
        )

    else:

        st.warning(
            f"🟡 {event['event'].upper()} DETECTED"
        )

    st.write(
        f"**Detection confidence:** "
        f"{event['confidence']}%"
    )

    st.write(
        f"**Assessment:** "
        f"{event['reason']}"
    )

    if event["signals"]:

        st.write(
            "**Environmental signals:**"
        )

        for signal in event["signals"]:

            st.write(
                f"✓ {signal}"
            )


# ==========================================================
# RENEWABLE ENERGY
# ==========================================================

st.subheader(
    "⚡ Renewable Energy Potential"
)

energy = decision["energy"]

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


# ==========================================================
# AUTOMATED ENERGY ALLOCATION
# ==========================================================

st.subheader(
    "⚡ Automated Energy Allocation"
)

st.caption(
    "The decision engine automatically redistributes "
    "renewable energy based on environmental conditions."
)

allocation_cols = st.columns(
    len(decision["energy_allocation"])
)

for column, allocation in zip(
    allocation_cols,
    decision["energy_allocation"],
):

    with column:

        st.metric(
            allocation["system"],
            f"{allocation['kw']} kW",
            f"{allocation['percent']}%",
        )


# ==========================================================
# RESOURCE LEDGER
# ==========================================================

resource_manager.show_resource_ledger()


# ==========================================================
# ADAPTIVE RESOURCE PRIORITIES
# ==========================================================

st.subheader(
    "🤖 Adaptive Resource Priorities"
)

if event["event"] == "Normal":

    st.info(
        "No environmental event is currently "
        "altering resource priorities."
    )

else:

    st.write(
        f"Because **{event['event']}** conditions "
        f"were detected, the decision engine has "
        f"automatically adjusted resource importance."
    )

    for resource in decision["resources"]:

        base = resource["priority"]

        boost = resource.get(
            "event_boost",
            0,
        )

        if boost > 0:

            st.write(
                f"**{resource['name']}** — "
                f"Base priority {base}/10 "
                f"→ **+{boost} event priority** "
                f"→ Decision score **{resource['score']}**"
            )


# ==========================================================
# RECOMMENDED ACTIONS
# ==========================================================

st.subheader(
    "🤖 Recommended Next Actions"
)

for i, recommendation in enumerate(
    decision["recommendations"],
    start=1,
):

    st.markdown(
        f"### {i}. "
        f"{recommendation['title']}"
    )

    st.write(
        recommendation["detail"]
    )