"""Resource management logic and Streamlit Resource Ledger UI."""

import uuid
import streamlit as st

class ResourceManager:
    def __init__(self):
        if "resources" not in st.session_state:
            st.session_state.resources = [
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
            ]
    # BACKEND: Get resources
    # -----------------------------
    def get_all_resources(self):
        return st.session_state.resources

    # BACKEND: Add resource
    # -----------------------------
    def add_resource(
        self,
        name,
        category,
        quantity,
        unit,
        horizon,
        priority,
    ):
        new_resource = {
            "id": str(uuid.uuid4()),
            "name": name,
            "category": category,
            "quantity": max(float(quantity), 0),
            "unit": unit,
            "horizon": horizon,
            "priority": max(1, min(int(priority), 10)),
        }

        st.session_state.resources.append(new_resource)
        return new_resource
    # -----------------------------
    # BACKEND: Update resource
    def update_resource(
        self,
        resource_id,
        name,
        category,
        quantity,
        unit,
        horizon,
        priority,
    ):
        for index, resource in enumerate(st.session_state.resources):
            if resource["id"] == resource_id:

                st.session_state.resources[index] = {
                    "id": resource_id,
                    "name": name,
                    "category": category,
                    "quantity": max(float(quantity), 0),
                    "unit": unit,
                    "horizon": horizon,
                    "priority": max(1, min(int(priority), 10)),
                }

                return True

        return False

    # -----------------------------
    # BACKEND: Delete resource
    def delete_resource(self, resource_id):
        for resource in st.session_state.resources:
            if resource["id"] == resource_id:
                st.session_state.resources.remove(resource)
                return True

        return False

    # -----------------------------
    # FRONTEND: Add Resource Dialog
    def show_add_dialog(self):

        @st.dialog("Add Resource")
        def add_dialog():
            with st.form("add_resource_form"):
                name = st.text_input("Resource Name")
                category = st.selectbox(
                    "Category",
                    ["Water", "Food", "Fuel", "Energy", "Medical", "Other"],
                )
                quantity = st.number_input(
                    "Quantity",
                    min_value=0.0,
                    value=0.0,
                )
                unit = st.text_input("Unit")

                horizon = st.text_input(
                    "Estimated Horizon",
                    placeholder="Example: 7 days",
                )
                priority = st.slider(
                    "Priority",
                    min_value=1,
                    max_value=10,
                    value=5,
                )
                submitted = st.form_submit_button("Add Resource")
                if submitted:
                    if name.strip() and unit.strip():

                        self.add_resource(
                            name=name,
                            category=category,
                            quantity=quantity,
                            unit=unit,
                            horizon=horizon,
                            priority=priority,
                        )

                        st.rerun()
                    else:
                        st.error(
                            "Please enter a resource name and unit."
                        )

        add_dialog()

    # -----------------------------
    # FRONTEND: Edit Resource Dialog
    def show_edit_dialog(self, resource):

        @st.dialog("Edit Resource")
        def edit_dialog():
            with st.form(f"edit_form_{resource['id']}"):
                name = st.text_input(
                    "Resource Name",
                    value=resource["name"],
                )
                category_options = [
                    "Water",
                    "Food",
                    "Fuel",
                    "Energy",
                    "Medical",
                    "Other",
                ]
                current_category = resource.get(
                    "category",
                    "Other",
                )
                category_index = (
                    category_options.index(current_category)
                    if current_category in category_options
                    else len(category_options) - 1
                )
                category = st.selectbox(
                    "Category",
                    category_options,
                    index=category_index,
                )
                quantity = st.number_input(
                    "Quantity",
                    min_value=0.0,
                    value=float(resource["quantity"]),
                )
                unit = st.text_input(
                    "Unit",
                    value=resource["unit"],
                )
                horizon = st.text_input(
                    "Estimated Horizon",
                    value=resource.get("horizon", ""),
                )
                priority = st.slider(
                    "Priority",
                    min_value=1,
                    max_value=10,
                    value=int(resource["priority"]),
                )
                submitted = st.form_submit_button(
                    "Save Changes"
                )
                if submitted:

                    self.update_resource(
                        resource_id=resource["id"],
                        name=name,
                        category=category,
                        quantity=quantity,
                        unit=unit,
                        horizon=horizon,
                        priority=priority,
                    )

                    st.rerun()

        edit_dialog()

    # -----------------------------
    # FRONTEND: Resource Ledger
    def show_resource_ledger(self):
        st.subheader("RESOURCE LEDGER")
        st.caption(
            "Manage island supplies and set priority levels for the "
            "decision engine."
        )

        if st.button("＋ Add Resource"):
            self.show_add_dialog()

        st.divider()

        # Table headers
        header = st.columns(
            [2.4, 1.3, 1.5, 1.3, 1, 0.5, 0.5]
        )

        with header[0]:
            st.markdown("**RESOURCE LINE**")

        with header[1]:
            st.markdown("**CATEGORY**")

        with header[2]:
            st.markdown("**ON HAND**")

        with header[3]:
            st.markdown("**HORIZON**")

        with header[4]:
            st.markdown("**PRIORITY**")

        st.divider()

        # Table rows
        for resource in self.get_all_resources():

            cols = st.columns(
                [2.4, 1.3, 1.5, 1.3, 1, 0.5, 0.5]
            )

            with cols[0]:
                st.markdown(f"**{resource['name']}**")
                st.caption(f"ID: {resource['id'][:8]}")

            with cols[1]:
                st.write(resource.get("category", "Other"))

            with cols[2]:
                st.markdown(
                    f"**{resource['quantity']}** "
                    f"{resource['unit']}"
                )

            with cols[3]:
                st.write(resource.get("horizon", "—"))

            with cols[4]:
                st.markdown(
                    f"**P{resource['priority']}** / 10"
                )

            with cols[5]:
                if st.button(
                    "✏️",
                    key=f"edit_{resource['id']}",
                    help="Edit resource",
                ):
                    self.show_edit_dialog(resource)

            with cols[6]:
                if st.button(
                    "🗑️",
                    key=f"delete_{resource['id']}",
                    help="Delete resource",
                ):
                    self.delete_resource(resource["id"])
                    st.rerun()

            # Line separating each row
            st.divider()