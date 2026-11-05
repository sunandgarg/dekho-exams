import asyncio
from contextvars import ContextVar

request_label = ContextVar("request_label", default="unset")
def blocking_receipt_lookup(identifier):
    return request_label.get() + ":" + identifier

async def main():
    token = request_label.set("review-7")
    try:
        print(await asyncio.to_thread(blocking_receipt_lookup, "R41"))
    finally:
        request_label.reset(token)

asyncio.run(main())
