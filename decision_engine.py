"""Combines environmental conditions, supply levels, and user priorities."""


def energy_potential(environment):
    solar_kw = round(environment["solar_radiation"] / 1000 * 4.0, 2)
    wind_kw = round(min(environment["wind_speed"] / 12, 1.5) * 1.8, 2)
    return {"solar_kw": solar_kw, "wind_kw": wind_kw, "total_kw": round(solar_kw + wind_kw, 2), "solar_level": "High" if solar_kw >= 2.5 else "Moderate" if solar_kw >= 1 else "Low", "wind_level": "High" if wind_kw >= 1.5 else "Moderate" if wind_kw >= 0.8 else "Low"}


def build_decision(environment, resources):
    energy = energy_potential(environment)
    ranked = []
    for resource in resources:
        quantity = max(float(resource["quantity"]), 0)
        scarcity = 1 / max(quantity, 1)
        score = resource["priority"] * (1 + min(scarcity * 100, 1.5))
        if resource["name"].lower() == "water" and environment["temperature"] >= 27:
            score += 3
        ranked.append({**resource, "score": round(score, 2)})
    ranked.sort(key=lambda item: item["score"], reverse=True)
    top = ranked[0]
    actions = [{"title": f"Prioritize {top['name'].lower()} operations", "detail": f"Priority {top['priority']}/10 leads the current ranking, with {top['quantity']} {top['unit']} available.", "type": "priority"}]
    if energy["solar_level"] == "High":
        actions.append({"title": "Run high-load tasks on solar", "detail": "Strong sunlight makes desalination, charging, and pumping the best use of current generation.", "type": "energy"})
    elif energy["wind_level"] == "High":
        actions.append({"title": "Use wind generation first", "detail": "Wind is the strongest renewable source right now; reserve fuel for critical backup.", "type": "energy"})
    else:
        actions.append({"title": "Conserve and store energy", "detail": "Renewable output is moderate or low, so defer flexible loads and protect the battery reserve.", "type": "energy"})
    actions.append({"title": "Store remaining energy", "detail": "Keep surplus in storage for the next low-production period and overnight demand.", "type": "storage"})
    return {"environment": environment, "energy": energy, "resources": ranked, "recommendations": actions}