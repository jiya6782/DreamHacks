"""Backend logic for managing island resources."""

from typing import Any, Dict, List
import uuid


class ResourceManager:
    def __init__(self):
        self.resources: List[Dict[str, Any]] = [
            {
                "id": "water",
                "name": "Fresh water",
                "category": "Water",
                "quantity": 1840,
                "unit": "liters",
                "horizon": "4.0 days",
                "priority": 10,
            },
            {
                "id": "food",
                "name": "Food stores",
                "category": "Food",
                "quantity": 126,
                "unit": "meals",
                "horizon": "8.0 days",
                "priority": 7,
            },
            {
                "id": "fuel",
                "name": "Diesel fuel",
                "category": "Fuel",
                "quantity": 420,
                "unit": "liters",
                "horizon": "14.0 days",
                "priority": 6,
            },
            {
                "id": "general",
                "name": "General supplies",
                "category": "General",
                "quantity": 86,
                "unit": "units",
                "horizon": "21.0 days",
                "priority": 5,
            },
        ]

    def get_all_resources(self) -> List[Dict[str, Any]]:
        """Return all resources."""
        return self.resources

    def get_resource(self, resource_id: str) -> Dict[str, Any] | None:
        """Find one resource by its ID."""
        for resource in self.resources:
            if resource["id"] == resource_id:
                return resource
        return None

    def add_resource(
        self,
        name: str,
        category: str,
        quantity: float,
        unit: str,
        horizon: str,
        priority: int,
    ) -> Dict[str, Any]:
        """Create and add a new resource."""

        resource = {
            "id": str(uuid.uuid4()),
            "name": name,
            "category": category,
            "quantity": quantity,
            "unit": unit,
            "horizon": horizon,
            "priority": priority,
        }

        self.resources.append(resource)
        return resource

    def update_resource(
        self,
        resource_id: str,
        name: str | None = None,
        category: str | None = None,
        quantity: float | None = None,
        unit: str | None = None,
        horizon: str | None = None,
        priority: int | None = None,
    ) -> Dict[str, Any] | None:
        """Update an existing resource."""

        resource = self.get_resource(resource_id)

        if resource is None:
            return None

        if name is not None:
            resource["name"] = name

        if category is not None:
            resource["category"] = category

        if quantity is not None:
            resource["quantity"] = max(quantity, 0)

        if unit is not None:
            resource["unit"] = unit

        if horizon is not None:
            resource["horizon"] = horizon

        if priority is not None:
            resource["priority"] = max(1, min(priority, 10))

        return resource

    def delete_resource(self, resource_id: str) -> bool:
        """Delete a resource by its ID."""

        resource = self.get_resource(resource_id)

        if resource is None:
            return False

        self.resources.remove(resource)
        return True