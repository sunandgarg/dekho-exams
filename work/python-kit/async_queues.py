import asyncio

async def pipeline():
    queue = asyncio.Queue(maxsize=2)
    completed = []
    async def consume():
        while True:
            receipt_id = await queue.get()
            try:
                if receipt_id is None:
                    return
                completed.append(receipt_id)
            finally:
                queue.task_done()
    worker = asyncio.create_task(consume())
    for receipt_id in (41, 42, 43):
        await queue.put(receipt_id)
    await queue.put(None)
    await queue.join()
    await worker
    return completed

print(asyncio.run(pipeline()))
