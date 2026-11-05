from functools import lru_cache

@lru_cache(maxsize=8)
def mutable_receipt_codes(region):
    return ["R-47"]

@lru_cache(maxsize=8)
def receipt_codes(region):
    return ("R-47",)

first_caller = mutable_receipt_codes("west")
first_caller.append("R-48")
print("shared_list", mutable_receipt_codes("west"))
print("stable_tuple", receipt_codes("west"))
print("same_cached_object", first_caller is mutable_receipt_codes("west"))
