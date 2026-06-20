from StandPy.generated.schemes_pb2 import GACHFBFBBEHDAAD
from StandPy.types.service import Service
import StandPy

class HandshakeRemoteService(Service):
    async def handshake(self: 'StandPy.StandClient', handshake: str):
        request = GACHFBFBBEHDAAD()
        request.GFCCADHDDFAFHFE = handshake
        self.raw.HandshakeRemoteService.encryptedHandshakeResponse(
            await self.send_request(
                *self.raw.HandshakeRemoteService.encryptedHandshakeRequest(request, self.cipher)
            ),
            self.cipher
        )
        return True
