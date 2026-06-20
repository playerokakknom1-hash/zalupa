from StandPy.generated.schemes_pb2 import (
    GetInventoryItemDefinitionsRequest,
    GetInventoryItemDefinitionsResponse,
    GetOtherPlayerItemsRequest,
    GetOtherPlayerItemsResponse,
    GetPlayerInventoryRequest,
    GetPlayerInventoryResponse,
)
from StandPy.types.service import Service
import StandPy

class InventoryRemoteService(Service):
    async def getOtherPlayerItemsEncrypted(
        self: 'StandPy.StandClient',
        gpid: str = "",
        item_definition_ids: list[int] | None = None,
    ) -> GetOtherPlayerItemsResponse:
        request = GetOtherPlayerItemsRequest()
        request.gpid = gpid
        if item_definition_ids:
            request.itemDefinitionIds.extend(item_definition_ids)

        response = await self.send_request(
            *self.raw.InventoryRemoteService.getOtherPlayerItemsEncryptedRequest(
                request, self.cipher
            )
        )

        return self.raw.InventoryRemoteService.getOtherPlayerItemsEncryptedResponse(response, self.cipher)

    async def getPlayerInventoryEncrypted(self: 'StandPy.StandClient') -> GetPlayerInventoryResponse:
        request = GetPlayerInventoryRequest()
        response = await self.send_request(
            *self.raw.InventoryRemoteService.getPlayerInventoryEncryptedRequest(
                request, self.cipher
            )
        )
        return self.raw.InventoryRemoteService.getPlayerInventoryEncryptedResponse(response, self.cipher)

    async def get_player_inventory(self: 'StandPy.StandClient') -> GetPlayerInventoryResponse:
        return await self.getPlayerInventoryEncrypted()

    async def getInventoryItemDefinitionsEncrypted(
        self: 'StandPy.StandClient',
        last_updated: str = "",
    ) -> GetInventoryItemDefinitionsResponse:
        request = GetInventoryItemDefinitionsRequest(lastUpdated=last_updated)
        response = await self.send_request(
            *self.raw.InventoryRemoteService.getInventoryItemDefinitionsEncryptedRequest(
                request, self.cipher
            )
        )
        return self.raw.InventoryRemoteService.getInventoryItemDefinitionsEncryptedResponse(
            response, self.cipher
        )

    async def get_inventory_item_definitions(
        self: 'StandPy.StandClient',
        last_updated: str = "",
    ) -> GetInventoryItemDefinitionsResponse:
        cache_key = "_inventory_item_definitions_cache"
        cached = getattr(self, cache_key, None)
        if cached is not None and last_updated in ("", cached.lastUpdated):
            return cached
        response = await self.getInventoryItemDefinitionsEncrypted(last_updated)
        if response.inventoryItemDefinitions:
            setattr(self, cache_key, response)
        return response

    async def get_other_player_items(
        self: 'StandPy.StandClient',
        gpid: str = "",
        item_definition_ids: list[int] | None = None,
    ) -> GetOtherPlayerItemsResponse:
        return await self.getOtherPlayerItemsEncrypted(gpid, item_definition_ids)
