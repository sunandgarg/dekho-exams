def accepted_totals(records):
    if not isinstance(records, list) or len(records) > 64:
        raise ValueError("record batch rejected")
    totals = {}
    for record in records:
        if not isinstance(record, dict) or set(record) != {"region", "amount"}:
            raise ValueError("record fields rejected")
        if not isinstance(record["region"], str) or record["region"] not in {"DEL", "BOM"}:
            raise ValueError("region rejected")
        amount = record["amount"]
        if type(amount) is not int or not 0 <= amount <= 1000000:
            raise ValueError("amount rejected")
        region = record["region"]
        totals[region] = totals.get(region, 0) + amount
    return totals

print(accepted_totals([{"region": "DEL", "amount": 125}, {"region": "DEL", "amount": 250}]))
try:
    accepted_totals([{"region": "DEL", "amount": 125}, {"region": "BOM", "amount": True}])
except ValueError:
    print("later record rejected; no totals returned")
