from StandPy.generated.schemes_pb2 import SubscribeRequest
import asyncio
from StandPy.types.service import Service
import StandPy

class BoltRemoteService(Service):
    async def subscribe(self: 'StandPy.StandClient', topic: str):
        subscribed_topics = getattr(self, "_subscribed_topics", None)
        if subscribed_topics is not None and topic in subscribed_topics:
            return True
        request = SubscribeRequest(topic=topic)
        self.raw.BoltRemoteService.subscribe2Response(
            await self.send_request(
                *self.raw.BoltRemoteService.subscribe2Request(request)
            )
        )
        if subscribed_topics is not None:
            subscribed_topics.add(topic)
        return True

    async def subscribe_trade(self: 'StandPy.StandClient', item_definition_id: int):
        return await self.subscribe(f"marketplace_trade_{item_definition_id}")

    async def subscribe_trades(self: 'StandPy.StandClient', item_definition_ids):
        await asyncio.gather(
            *(self.subscribe_trade(int(item_id)) for item_id in item_definition_ids)
        )
        return True
