import asyncio
from contextlib import aclosing

async def review_stream(released):
    try:
        yield "R-0041"
        yield "R-0042"
    finally:
        released.append("producer closed")

async def first_review():
    released = []
    async with aclosing(review_stream(released)) as stream:
        async for receipt_id in stream:
            print(receipt_id)
            break
    print(released)

asyncio.run(first_review())
