import asyncio
import io
import unittest

events = []
class QueueCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.queue = asyncio.Queue()
        events.append("setup")
    async def test_receipt(self):
        await self.queue.put("R41")
        self.assertEqual(await self.queue.get(), "R41")
        events.append("test")
    async def asyncTearDown(self):
        self.assertTrue(self.queue.empty())
        events.append("cleanup")

result = unittest.TextTestRunner(stream=io.StringIO()).run(
    unittest.defaultTestLoader.loadTestsFromTestCase(QueueCase))
print("passed:", result.wasSuccessful())
print("events:", events)
