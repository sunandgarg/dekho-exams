import asyncio
from contextvars import ContextVar

tenant_id = ContextVar("tenant_id")

async def read_tenant(gate):
    await gate.wait()
    return tenant_id.get()

async def main():
    token = tenant_id.set("north-47")
    try:
        gate = asyncio.Event()
        reader = asyncio.create_task(read_tenant(gate))
        tenant_id.set("south-47")
        gate.set()
        print("task", await reader)
        print("parent", tenant_id.get())
    finally:
        tenant_id.reset(token)

asyncio.run(main())
