import streamlit as st

from decision_engine import build_decision
from environmental_simulator import EnvironmentalSimulator
from resource_manager import ResourceManager


# --------------------------------------------------
# App configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Island Resource Dashboard",
    page_icon="🌱",
    layout="wide",
)


# --------------------------------------------------
# Simulation state
# --------------------------------------------------

@st.cache_resource
def get_simulator():
    return EnvironmentalSimulator()


simulator = get_simulator()


# --------------------------------------------------
# Resource manager
# --------------------------------------------------

@st.cache_resource
def get_resource_manager():
    return ResourceManager()


resource_manager = get_resource_manager()


# --------------------------------------------------
# Header
# --------------------------------------------------

st.title("🌱 Island Resource Dashboard")
st.caption("Simulation-first environmental resource management")


# --------------------------------------------------
# Controls
# --------------------------------------------------

col1, col2 = st.columns([1, 4])

with col1:
    if st.button("🔄 Advance Simulation", use_container_width=True):
        simulator.advance()
        st.rerun()


# --------------------------------------------------
# Get current data
# --------------------------------------------------

environment = simulator.snapshot()

resources = resource_manager.get_all_resources()

decision = build_decision(
    environment,
    resources,
)


# --------------------------------------------------
# Simulation status
# --------------------------------------------------

st.subheader("Simulation Status")

cols = st.columns(5)

cols[0].metric(
    "Solar Radiation",
    f"{environment['solar_radiation']} W/m²"
)

cols[1].metric(
    "Wind Speed",
    f"{environment['wind_speed']} m/s"
)

cols[2].metric(
    "Temperature",
    f"{environment['temperature']} °C"
)

cols[3].metric(
    "Weather",
    environment["weather"]
)

cols[4].metric(
    "Time",
    environment["time_of_day"]
)


# --------------------------------------------------
# Renewable energy
# --------------------------------------------------

st.subheader("⚡ Renewable Energy Potential")

energy = decision["energy"]

energy_cols = st.columns(3)

energy_cols[0].metric(
    "☀️ Solar",
    f"{energy['solar_kw']} kW",
    energy["solar_level"]
)

energy_cols[1].metric(
    "🌬️ Wind",
    f"{energy['wind_kw']} kW",
    energy["wind_level"]
)

energy_cols[2].metric(
    "⚡ Total Available",
    f"{energy['total_kw']} kW"
)


# --------------------------------------------------
# Resources
# --------------------------------------------------

st.subheader("📦 Resource Ledger")

for resource in resources:

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.write(f"**{resource['name']}**")

    with col2:
        st.write(
            f"{resource['quantity']} "
            f"{resource['unit']}"
        )

    with col3:
        st.write(
            f"Priority: {resource['priority']}/10"
        )

    with col4:
        st.write(
            resource.get("category", "Other")
        )


# --------------------------------------------------
# Recommended actions
# --------------------------------------------------

st.subheader("🤖 Recommended Next Actions")

for i, recommendation in enumerate(
    decision["recommendations"],
    start=1,
):
    st.markdown(
        f"### {i}. {recommendation['title']}"
    )
    st.write(recommendation["detail"])