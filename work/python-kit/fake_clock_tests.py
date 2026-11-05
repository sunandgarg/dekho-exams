def active_lease(now_ms, expiry_ms):
    if type(now_ms) is not int or type(expiry_ms) is not int or not 0 <= now_ms <= 100000 or not 0 <= expiry_ms <= 100000:
        raise ValueError("bounded millisecond times")
    return now_ms < expiry_ms

for controlled_now in (499, 500, 501):
    print(controlled_now, active_lease(controlled_now, 500))
try:
    active_lease(True, 500)
except ValueError:
    print("boolean clock rejected")
