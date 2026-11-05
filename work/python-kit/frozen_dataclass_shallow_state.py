from dataclasses import FrozenInstanceError, dataclass

@dataclass(frozen=True)
class DispatchPlan:
    route_ids: list[str]

plan = DispatchPlan(["route-47"])
plan.route_ids.append("route-48")
print("routes:", plan.route_ids)
try:
    plan.route_ids = []
except FrozenInstanceError:
    print("field rebinding rejected")
