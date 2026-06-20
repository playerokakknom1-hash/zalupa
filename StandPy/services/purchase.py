from StandPy.generated.schemes_pb2 import (
    CancelRequestRequest,
    CreatePurchaseRequestRequest,
    CreatePurchaseRequestResponse,
    CreateSaleRequest,
    CreatePurchaseRequestBySaleRequest,
    CreatePurchaseRequestBySaleResponse,
    GetPlayerOpenRequestsRequest,
    GetPlayerProcessingRequestRequest,
    GetTradeRequest,
    GetTradeOpenSaleRequestsRequest,
)
from StandPy.errors import StandPyRPCException
from StandPy.types.service import Service
import asyncio
import StandPy

class MarketplaceRemoteService(Service):
    PURCHASE_BY_SALE_CODE = 12
    CREATE_PURCHASE_CODE = 11
    _PURCHASE_SALE_ID_TAG = b"\x0a"

    @staticmethod
    def _encode_varint(value: int) -> bytes:
        result = bytearray()
        while value > 0x7F:
            result.append((value & 0x7F) | 0x80)
            value >>= 7
        result.append(value)
        return bytes(result)

    def _purchase_request_payload(self: 'StandPy.StandClient', sale_id: str) -> bytes:
        sale_id_bytes = sale_id.encode()
        return self._PURCHASE_SALE_ID_TAG + self._encode_varint(len(sale_id_bytes)) + sale_id_bytes

    async def _purchase_by_sale_payload(
        self: 'StandPy.StandClient',
        request_payload: bytes,
        timeout: float | None = None,
    ) -> str:
        response = await self.send_request(self.PURCHASE_BY_SALE_CODE, request_payload, timeout=timeout)
        if response.exception.code:
            raise StandPyRPCException(response.exception)
        if not response.data:
            raise TimeoutError("empty purchase response")
        response = CreatePurchaseRequestBySaleResponse.FromString(response.data[0].one)
        purchase_id = response.purchaseRequestId.strip()
        if not purchase_id:
            raise RuntimeError("empty purchase id")
        return purchase_id

    async def createPurchaseRequestBySale(self: 'StandPy.StandClient', sale_id: str):
        request = CreatePurchaseRequestBySaleRequest(saleId=sale_id)
        response = await self.send_request(
            *self.raw.MarketplaceRemoteService.createPurchaseRequestBySale2Request(request)
        )
        return self.raw.MarketplaceRemoteService.createPurchaseRequestBySale2Response(response)

    async def purchase_by_sale(self: 'StandPy.StandClient', sale_id: str):
        return await self.createPurchaseRequestBySale(sale_id)

    async def purchase_by_sale_id(
        self: 'StandPy.StandClient',
        sale_id: str,
        timeout: float | None = None,
    ) -> str:
        return await self._purchase_by_sale_payload(
            self._purchase_request_payload(sale_id),
            timeout=timeout,
        )

    async def fast_purchase(
        self: 'StandPy.StandClient',
        sale_id: str,
        retries: int = 3,
        timeout: float = 1.5,
        retry_rpc_errors: bool = False,
    ) -> str:
        last_error = None
        request = self._purchase_request_payload(sale_id)
        attempts = max(1, retries)
        for _ in range(attempts):
            try:
                return await self._purchase_by_sale_payload(request, timeout=timeout)
            except StandPyRPCException as exc:
                if not retry_rpc_errors:
                    raise
                last_error = exc
            except Exception as exc:
                last_error = exc
        raise last_error

    async def bulk_purchase(
        self: 'StandPy.StandClient',
        sale_ids: list[str],
        retries: int = 1,
        timeout: float | None = None,
    ):
        return await asyncio.gather(
            *(
                self.fast_purchase(
                    sale_id,
                    retries=retries,
                    timeout=self._request_timeout if timeout is None else timeout,
                )
                for sale_id in sale_ids
            ),
            return_exceptions=True,
        )

    async def create_purchase_request(
        self: 'StandPy.StandClient',
        item_definition_id: int,
        price: float,
        quantity: int = 1,
        timeout: float | None = None,
    ) -> str:
        request = CreatePurchaseRequestRequest(
            itemDefinitionId=item_definition_id,
            price=price,
            quantity=quantity,
        )
        response = await self.send_request(
            self.CREATE_PURCHASE_CODE,
            request.SerializeToString(),
            timeout=timeout,
        )
        if response.exception.code:
            raise StandPyRPCException(response.exception)
        if not response.data:
            raise TimeoutError("empty create purchase response")
        parsed = CreatePurchaseRequestResponse.FromString(response.data[0].one)
        purchase_id = parsed.purchaseRequestId.strip()
        if not purchase_id:
            raise RuntimeError("empty purchase request id")
        return purchase_id

    async def create_sale(self: 'StandPy.StandClient', item_id: int, price: float):
        request = CreateSaleRequest(itemId=item_id, price=price)
        response = await self.send_request(
            *self.raw.MarketplaceRemoteService.createSaleRequest(request)
        )
        return self.raw.MarketplaceRemoteService.createSaleResponse(response)

    async def cancel_request(
        self: 'StandPy.StandClient',
        request_id: str,
        timeout: float | None = None,
    ):
        request = CancelRequestRequest(requestId=request_id)
        response = await self.send_request(
            *self.raw.MarketplaceRemoteService.cancelRequest2Request(request),
            timeout=timeout,
        )
        return self.raw.MarketplaceRemoteService.cancelRequest2Response(response)

    async def get_player_open_requests(self: 'StandPy.StandClient'):
        request = GetPlayerOpenRequestsRequest()
        response = await self.send_request(
            *self.raw.MarketplaceRemoteService.getPlayerOpenRequests2Request(request)
        )
        return self.raw.MarketplaceRemoteService.getPlayerOpenRequests2Response(response)

    async def get_player_processing_requests(self: 'StandPy.StandClient'):
        request = GetPlayerProcessingRequestRequest()
        response = await self.send_request(
            *self.raw.MarketplaceRemoteService.getPlayerProcessingRequests2Request(request)
        )
        return self.raw.MarketplaceRemoteService.getPlayerProcessingRequests2Response(response)

    async def get_trade(
        self: 'StandPy.StandClient',
        item_definition_id: int,
        timeout: float | None = None,
    ):
        request = GetTradeRequest(id=item_definition_id)
        response = await self.send_request(
            *self.raw.MarketplaceRemoteService.getTrade2Request(request),
            timeout=timeout,
        )
        return self.raw.MarketplaceRemoteService.getTrade2Response(response)

    async def get_trade_open_sale_requests(
        self: 'StandPy.StandClient',
        item_definition_id: int,
        page: int = 0,
        size: int = 20,
        timeout: float | None = None,
    ):
        request = GetTradeOpenSaleRequestsRequest(
            id=item_definition_id,
            page=page,
            size=size,
        )
        response = await self.send_request(
            *self.raw.MarketplaceRemoteService.getTradeOpenSaleRequests2Request(request),
            timeout=timeout,
        )
        return self.raw.MarketplaceRemoteService.getTradeOpenSaleRequests2Response(response)
