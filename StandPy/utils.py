import asyncio
from collections.abc import Coroutine

def run_async(func: Coroutine):
    if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(func)


run_on_windows = run_async
