from functools import lru_cache

PRICES = {("standard", 1): 125, ("standard", 2): 150}
@lru_cache(maxsize=2)
def unit_price(receipt_class, revision):
    return PRICES[(receipt_class, revision)]

print(unit_price("standard", 1))
print(unit_price("standard", 1))
print(unit_price("standard", 2))
info = unit_price.cache_info()
print("hits:", info.hits, "retained:", info.currsize)
unit_price.cache_clear()
print("after clear:", unit_price.cache_info().currsize)
