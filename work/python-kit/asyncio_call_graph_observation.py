import asyncio

async def inspect_receipt():
    graph = asyncio.capture_call_graph(depth=0)
    return (graph.future is asyncio.current_task(),
            bool(graph.awaited_by))

async def main():
    async with asyncio.TaskGroup() as group:
        inspection = group.create_task(inspect_receipt())
    current, awaited = inspection.result()
    print("current_task", current)
    print("awaited_by_parent", awaited)

asyncio.run(main())
