from StandPy.schemes.messages_pb2 import ServerMsg


class Parser:
    @staticmethod
    def _encode_varint(value: int) -> bytes:
        result = bytearray()
        while value > 0x7F:
            result.append((value & 0x7F) | 0x80)
            value >>= 7
        result.append(value)
        return bytes(result)

    @staticmethod
    def new_msg(uuid: str, code: int, payload: bytes) -> bytes:
        request_id = uuid.encode()
        data = b"" if not payload else (
            b"\x1a" + Parser._encode_varint(len(payload)) + payload
        )
        return b"".join((
            b"\x0a", Parser._encode_varint(len(request_id)), request_id,
            b"\x22", Parser._encode_varint(len(data)), data,
            b"\x28", Parser._encode_varint(code),
        ))

    @staticmethod
    def parse_response(data: bytes) -> ServerMsg:
        return ServerMsg.FromString(data)
