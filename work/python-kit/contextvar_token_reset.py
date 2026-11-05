from contextvars import ContextVar

request_id = ContextVar("request_id", default="unbound")
outer_token = request_id.set("R-47")
try:
    inner_token = request_id.set("R-48")
    try:
        print("nested", request_id.get())
    finally:
        request_id.reset(inner_token)
    print("outer", request_id.get())
finally:
    request_id.reset(outer_token)

print("restored", request_id.get())
try:
    request_id.reset(outer_token)
except RuntimeError:
    print("second_reset_rejected", True)
