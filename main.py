import streamlit as st

from decision_engine import build_decision
from environmental_simulator import EnvironmentalSimulator


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
# Resources
# --------------------------------------------------

if "resources" not in st.session_state:
    st.session_state.resources = [
        {
            "name": "Water",
            "quantity": 420,
            "unit": "L",
            "priority": 10,
        },
        {
            "name": "Food",
            "quantity": 160,
            "unit": "kg",
            "priority": 7,
        },
        {
            "name": "Fuel",
            "quantity": 85,
            "unit": "L",
            "priority": 6,
        },
        {
            "name": "General supplies",
            "quantity": 34,
            "unit": "boxes",
            "priority": 5,
        },
    ]


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
# Current decision
# --------------------------------------------------

decision = build_decision(
    simulator.snapshot(),
    st.session_state.resources,
)


# --------------------------------------------------
# Simulation status
# --------------------------------------------------

st.subheader("Simulation Status")

status = simulator.snapshot()

if isinstance(status, dict):
    cols = st.columns(len(status))

    for column, (key, value) in zip(cols, status.items()):
        with column:
            st.metric(
                label=str(key).replace("_", " ").title(),
                value=str(value),
            )
else:
    st.write(status)


# --------------------------------------------------
# Resources
# --------------------------------------------------

st.subheader("Resources")

for resource in st.session_state.resources:
    name = resource.get("name", "Unknown")
    quantity = resource.get("quantity", 0)
    unit = resource.get("unit", "")
    priority = resource.get("priority", 0)

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        st.write(f"**{name}**")

    with col2:
        st.write(f"{quantity} {unit}")

    with col3:
        st.write(f"Priority: {priority}")


# --------------------------------------------------
# Decision
# --------------------------------------------------

st.subheader("Decision")

if isinstance(decision, dict):
    st.json(decision)
else:
    st.write(decision)


# --------------------------------------------------
# Resource editor
# --------------------------------------------------

with st.expander("Edit Resources"):
    edited_resources = st.data_editor(
        st.session_state.resources,
        num_rows="dynamic",
        use_container_width=True,
    )

    if st.button("Save Resources"):
        st.session_state.resources = edited_resources
        st.success("Resources updated.")
        st.rerun()