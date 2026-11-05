import asyncio

async def cached_receipt_score():
    return 47

async def inspect_creation():
    loop = asyncio.get_running_loop()
    ordinary = asyncio.create_task(cached_receipt_score())
    print("ordinary_done_at_creation", ordinary.done())
    print("ordinary_result", await ordinary)

    prior_factory = loop.get_task_factory()
    loop.set_task_factory(asyncio.eager_task_factory)
    try:
        eager = asyncio.create_task(cached_receipt_score())
        print("eager_done_at_creation", eager.done())
        print("eager_result", await eager)
    finally:
        loop.set_task_factory(prior_factory)

asyncio.run(inspect_creation())
