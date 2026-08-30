"""Resource ledger for the island simulation."""

import streamlit as st


DEFAULT_RESOURCES = [
    {
        "id": "water",
        "name": "Fresh Water",
        "category": "Water",
        "quantity": 1840.0,
        "unit": "liters",
        "horizon": "4.0 days",
        "priority": 10,
    },
    {
        "id": "food",
        "name": "Food Stores",
        "category": "Food",
        "quantity": 126.0,
        "unit": "meals",
        "horizon": "8.0 days",
        "priority": 7,
    },
    {
        "id": "fuel",
        "name": "Diesel Fuel",
        "category": "Fuel",
        "quantity": 420.0,
        "unit": "liters",
        "horizon": "14.0 days",
        "priority": 6,
    },
    {
        "id": "supplies",
        "name": "General Supplies",
        "category": "General",
        "quantity": 86.0,
        "unit": "units",
        "horizon": "21.0 days",
        "priority": 5,
    },
    {
        "id": "shelter",
        "name": "Emergency Shelter",
        "category": "General",
        "quantity": 24.0,
        "unit": "spaces",
        "horizon": "2.0 days",
        "priority": 5,
    },
]


class ResourceManager:
    """Thin wrapper around st.session_state.resources."""

    def __init__(self):

        if "resources" not in st.session_state:
            st.session_state.resources = [
                dict(resource) for resource in DEFAULT_RESOURCES
            ]

    def get_all_resources(self):
        return st.session_state.resources

    def update_quantity(self, resource_id: str, quantity: float) -> None:

        for resource in st.session_state.resources:
            if resource["id"] == resource_id:
                resource["quantity"] = max(quantity, 0)
                break

    def show_resource_ledger(self) -> None:

        st.subheader("📦 Resource Ledger")

        for resource in st.session_state.resources:

            col1, col2, col3 = st.columns([3, 2, 2])

            with col1:
                st.markdown(f"**{resource['name']}**")
                st.caption(resource.get("category", ""))

            with col2:
                st.write(f"{resource['quantity']} {resource['unit']}")
                st.caption(f"Runs out in ~{resource.get('horizon', 'unknown')}")

            with col3:
                new_quantity = st.number_input(
                    "Adjust quantity",
                    min_value=0.0,
                    value=float(resource["quantity"]),
                    key=f"qty_{resource['id']}",
                    label_visibility="collapsed",
                )

                if new_quantity != resource["quantity"]:
                    self.update_quantity(resource["id"], new_quantity)
                    st.rerun()