import asyncio
from contextvars import ContextVar

receipt_context = ContextVar("receipt_context", default="unassigned")
async def inspect_receipt(receipt_id):
    token = receipt_context.set(receipt_id)
    try:
        await asyncio.sleep(0)
        return receipt_context.get()
    finally:
        receipt_context.reset(token)

async def inspect_batch():
    token = receipt_context.set("batch-DEL")
    try:
        print(await asyncio.gather(inspect_receipt("R-0041"), inspect_receipt("R-0042")))
        print("parent:", receipt_context.get())
    finally:
        receipt_context.reset(token)

asyncio.run(inspect_batch())
print("outside:", receipt_context.get())
