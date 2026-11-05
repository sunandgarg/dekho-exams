by_route = {}
route_receipts = by_route.setdefault("north", [])
route_receipts.append("R41")
same_list = by_route.setdefault("north", [])
same_list.append("R42")
print(by_route)
print(route_receipts is same_list)
print(route_receipts is by_route["north"])
