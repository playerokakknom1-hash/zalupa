import logging
import asyncio
from collections import defaultdict
from .types.update import Update
from .listener import Listener

logger = logging.getLogger(__name__)

class Dispatcher:
    __slots__ = ("_client", "listeners")

    def __init__(self, client):
        self._client = client
        self.listeners: dict = defaultdict(list)

    def add_listener(self, listener: Listener):
        self.listeners[listener.event].append(listener)

    async def call_listeners(self, update: Update):
        listeners = self.listeners.get(update.event)
        if not listeners:
            return
        if len(listeners) == 1:
            try:
                await listeners[0].call(self._client, update)
            except Exception as result:
                logger.error(
                    "Listener failed: %s",
                    result,
                    exc_info=(type(result), result, result.__traceback__),
                )
            return
        results = await asyncio.gather(
            *(listener.call(self._client, update) for listener in listeners),
            return_exceptions=True,
        )
        for result in results:
            if isinstance(result, BaseException):
                logger.error(
                    "Listener failed: %s",
                    result,
                    exc_info=(type(result), result, result.__traceback__),
                )
