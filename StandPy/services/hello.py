from secrets import token_bytes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from StandPy.generated.schemes_pb2 import CHGACEEHFADEDHH
from StandPy.types.service import Service
import StandPy

class HelloRemoteService(Service):
    def __init__(self):
        super().__init__()
        self._rsa_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=1024
        )
        self._public_nums = self._rsa_key.public_key().public_numbers()

    async def hello(self: 'StandPy.StandClient'):
        iv = token_bytes(16)
        request = CHGACEEHFADEDHH()
        request.DCAGCDFCHBBDCDB = self._public_nums.n.to_bytes(128, "big")
        request.GABAFEDDDBEGGAE = self._public_nums.e.to_bytes(3, "big")
        request.CGCGBGBEGCADABH = iv
        response = self.raw.HelloRemoteService.helloResponse(
            await self.send_request(
                *self.raw.HelloRemoteService.helloRequest(request, self.cipher)
            ),
            self.cipher
        )
        key = self._rsa_key.decrypt(response.FBHHACGFCHFEEED, padding.PKCS1v15())
        self.cipher.new_aes_cipher(key, iv)
        return True
