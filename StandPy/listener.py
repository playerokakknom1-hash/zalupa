from collections.abc import Callable
from StandPy.types.update import Update
from StandPy.enums.events import BaseEvent

class Listener:
    __slots__ = ("_callback",)

    event: BaseEvent = BaseEvent.UNKNOWN

    def __init__(self, callback: Callable):
        self._callback = callback

    async def call(self, client, update: Update):
        await self._callback(client, update)
