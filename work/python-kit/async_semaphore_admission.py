import asyncio

async def main():
    gate = asyncio.Semaphore(2)
    active = 0
    peak = 0

    async def fetch_status(parcel_id):
        nonlocal active, peak
        async with gate:
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0)
            active -= 1
            return parcel_id

    async with asyncio.TaskGroup() as group:
        tasks = [group.create_task(fetch_status(parcel_id))
                 for parcel_id in ("P-47", "P-48", "P-49", "P-50")]
    print("scheduled:", len(tasks))
    print("peak:", peak)
    print("results:", [task.result() for task in tasks])

asyncio.run(main())
