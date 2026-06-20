from StandPy.generated.schemes_pb2 import GetPlayerRequest, SetPlayerNameRequest
from StandPy.types.service import Service
import StandPy


class PlayerRemoteService(Service):
    async def get_player(self: 'StandPy.StandClient'):
        request = GetPlayerRequest()
        response = await self.send_request(
            *self.raw.PlayerRemoteService.getPlayer2Request(request)
        )
        return self.raw.PlayerRemoteService.getPlayer2Response(response)

    async def set_player_name(self: 'StandPy.StandClient', name: str):
        request = SetPlayerNameRequest(newName=name)
        response = await self.send_request(
            *self.raw.PlayerRemoteService.setPlayerName2Request(request)
        )
        return self.raw.PlayerRemoteService.setPlayerName2Response(response)
