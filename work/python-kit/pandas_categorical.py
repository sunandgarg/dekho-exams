import pandas as pd

states = ["pending", "accepted", "rejected"]
dtype = pd.CategoricalDtype(states, ordered=True)
received = pd.Series(["accepted", "pending", "rejected"], dtype="string")
if not received.isin(states).all(): raise ValueError("unknown state rejected")
accepted = received.astype(dtype)
print("workflow order:", accepted.sort_values().astype(str).tolist())
unchecked = pd.Series(["archived"], dtype="string").astype(dtype)
print("unchecked unknown becomes missing:", bool(unchecked.isna().iloc[0]))
print("explicit validation:", bool(pd.Series(["archived"]).isin(states).all()))
