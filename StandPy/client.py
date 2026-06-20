import asyncio
import ssl
import socket
from threading import Thread, Event
from itertools import count
import lz4.block
from .dispatcher import Dispatcher
from .cipher import StandPyCipher
from .events import BaseEvents
from .types.extras import ConnectionInfo
from .generated import Generated, CADATA, GENERATED_UPDATES, UPDATE_INDEX
from .services import Services
from .logging import StandPyLoggers
from .updates import Connected
from .parser import Parser
from .schemes.messages_pb2 import Response, ServerMsg
from .errors import StandPyRPCException

class StandClient(Thread, Services, BaseEvents, Generated):
    SERVER_HOST = "server.boltgaming.io"
    SERVER_PORT = 2223
    REQUEST_TIMEOUT = 5
    READ_TIMEOUT = 3.0
    PING_TIMEOUT = 5.0
    PING_INTERVAL = 5.0
    _ssl_context = None

    def __init__(self, handshake: str, request_timeout: float | None = None):
        Thread.__init__(self, daemon=True)
        Services.__init__(self)
        self._handshake = handshake
        self._request_timeout = request_timeout or self.REQUEST_TIMEOUT
        self._dp = Dispatcher(self)
        self._reader = None
        self._writer = None
        self._loop = None
        self._running = False
        self._connect_info = ConnectionInfo()
        self._pending_ping = None
        self._pending_requests = {}
        self._request_ids = count(1)
        self.scan_cache: dict[int, list] = {}
        self.scan_cache_enabled = True
        self._subscribed_topics: set[str] = set()
        self._connected = Event()
        self._disconnected = Event()
        self._send_lock = None
        self.cipher = StandPyCipher()
        self._logger = StandPyLoggers.get_logger(StandClient.__name__)

    @property
    def logger(self):
        return self._logger

    def _create_task(self, coro):
        task = asyncio.create_task(coro)
        task.add_done_callback(self._log_task_error)
        return task

    def _log_task_error(self, task: asyncio.Task):
        try:
            task.result()
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            self._logger.exception(f"Background task failed: {exc}")

    async def _connect(self):
        await self._disconnect()
        self._connected.clear()
        self._reader, self._writer = await asyncio.open_connection(
            self.SERVER_HOST, self.SERVER_PORT, ssl=self._get_ssl_context()
        )
        sock = self._writer.get_extra_info("socket")
        if sock is not None:
            try:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            except OSError:
                pass
        self._running = True
        self._connected.set()

    @classmethod
    def _get_ssl_context(cls):
        if cls._ssl_context is None:
            ctx = ssl.create_default_context()
            if CADATA:
                ctx.load_verify_locations(cadata=CADATA)
            else:
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            cls._ssl_context = ctx
        return cls._ssl_context

    async def _disconnect(self):
        self._connected.clear()
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
            self._writer = None
            self._reader = None
        self._disconnected.set()

    def run(self):
        if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(self._run())

    async def _run(self):
        self._loop = asyncio.get_event_loop()
        self._pending_ping = asyncio.Event()
        self._send_lock = asyncio.Lock()
        try:
            await self._connect()
            self._create_task(self._initialize())
            await self._read_loop()
        except Exception as exc:
            self._logger.exception(f"Client loop failed: {exc}")
        finally:
            self._running = False
            await self._disconnect()

    async def _initialize(self):
        try:
            await self.hello()
            await self.handshake(self._handshake)
            self._create_task(self._ping_loop())
            await self._dp.call_listeners(Connected())
        except StandPyRPCException:
            self._logger.critical("Authorization failed!")
            self._running = False

    async def _read_loop(self):
        while self._running:
            length = await self._read_header()
            if length <= 0:
                continue
            data = await self._read_exactly(length)
            if not data:
                continue
            if data == b'\x01':
                self._pending_ping.set()
                continue
            self._create_task(self._handle_data(data))
        self._running = False

    async def _handle_data(self, data: bytes):
        await self._handle_msg(Parser.parse_response(data))

    async def _ping_loop(self):
        self._logger.extra = self._connect_info
        while self._running:
            self._pending_ping.clear()
            t0 = self._loop.time()
            if not await self._send_payload(b'\x01'):
                self._logger.critical("Ping send failed!")
                self._running = False
                break
            try:
                await asyncio.wait_for(self._pending_ping.wait(), timeout=self.PING_TIMEOUT)
            except asyncio.TimeoutError:
                self._logger.critical("Ping timeout!")
                self._running = False
                break
            self._connect_info.ping = int((self._loop.time() - t0) * 1000)
            await asyncio.sleep(self.PING_INTERVAL)

    async def _read_exactly(self, size: int):
        try:
            return await asyncio.wait_for(self._reader.readexactly(size), timeout=self.READ_TIMEOUT)
        except asyncio.TimeoutError:
            return None
        except asyncio.IncompleteReadError:
            self._running = False
            self._logger.critical("Connection closed!")
            return None
        except Exception as e:
            self._logger.exception(f"Read error: {e}")
            return None

    async def _read_header(self) -> int:
        hdr = await self._read_exactly(4)
        if not hdr:
            return -1
        return int.from_bytes(hdr, byteorder='big')

    async def _handle_msg(self, msg: ServerMsg):
        for response in msg.responses:
            fut = self._pending_requests.pop(response.id, None)
            if fut and not fut.done():
                fut.set_result(response)
        event_call = None
        event_calls = None
        for event in msg.events:
            update_index = UPDATE_INDEX.get(event.code)
            if update_index is not None:
                update_cls = GENERATED_UPDATES[event.code][update_index]
                if update_cls.event not in self._dp.listeners and not self.scan_cache_enabled:
                    continue
                update = update_cls(event.params.one)
                if self.scan_cache_enabled:
                    self._update_scan_cache(update)
                if update.event in self._dp.listeners:
                    call = self._dp.call_listeners(update)
                    if event_call is None and event_calls is None:
                        event_call = call
                    else:
                        if event_calls is None:
                            event_calls = [event_call]
                            event_call = None
                        event_calls.append(call)
        if event_calls is not None:
            await asyncio.gather(*event_calls, return_exceptions=True)
        elif event_call is not None:
            await event_call
        for compressed in msg.compressed_instances:
            raw = lz4.block.decompress(
                compressed.compressed,
                uncompressed_size=compressed.uncompressed_size
            )
            await self._handle_msg(Parser.parse_response(raw))

    def _update_scan_cache(self, update):
        data = getattr(update, "data", None)
        if data is None:
            return

        trade = getattr(data, "trade", None)
        if trade is not None and getattr(trade, "id", 0):
            self.scan_cache[int(trade.id)] = [trade]
            return

        request = getattr(data, "request", None)
        item_definition_id = getattr(request, "itemDefinitionId", 0)
        if not request or not item_definition_id:
            return

        item_definition_id = int(item_definition_id)
        cached = self.scan_cache.setdefault(item_definition_id, [])
        request_id = getattr(request, "id", "")
        origin_id = getattr(request, "originId", "")
        close_date = getattr(request, "closeDate", 0)

        if close_date or origin_id:
            ids_to_remove = {value for value in (request_id, origin_id) if value}
            if ids_to_remove:
                self.scan_cache[item_definition_id] = [
                    item for item in cached
                    if getattr(item, "id", None) not in ids_to_remove
                ]
            return

        if request_id:
            for idx, item in enumerate(cached):
                if getattr(item, "id", None) == request_id:
                    cached[idx] = request
                    break
            else:
                cached.append(request)

    async def send_request(self, code: int, request: bytes, timeout: float | None = None):
        uuid = str(next(self._request_ids))
        fut = self._loop.create_future()
        self._pending_requests[uuid] = fut
        if not await self._send_payload(Parser.new_msg(uuid, code, request)):
            self._pending_requests.pop(uuid, None)
            raise ConnectionError("Connection lost.")
        try:
            result = await asyncio.wait_for(
                fut,
                timeout=self._request_timeout if timeout is None else timeout,
            )
        except asyncio.TimeoutError:
            self._logger.warning(f"Request {uuid} timed out.")
            result = Response()
        finally:
            self._pending_requests.pop(uuid, None)
        return result

    async def _send_payload(self, payload: bytes) -> bool:
        if not self._running or not self._writer:
            return False
        async with self._send_lock:
            try:
                length = len(payload)
                self._writer.write(length.to_bytes(4, byteorder='big') + payload)
                await self._writer.drain()
                return True
            except (BrokenPipeError, ConnectionResetError):
                self._logger.critical("Connection lost!")
                self._running = False
                return False
            except Exception as e:
                self._logger.exception(f"Send error: {e}")
                return False

    def _close_writer(self):
        if self._writer:
            self._writer.close()

    def start(self, timeout: float = 10.0):
        self._connected.clear()
        self._disconnected.clear()
        super().start()
        if not self._connected.wait(timeout):
            raise TimeoutError("Client connection timed out.")

    def idle(self):
        self.join()

    def stop(self):
        if not self._running:
            return
        self._disconnected.clear()
        self._running = False
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._close_writer)
        self._disconnected.wait(self.READ_TIMEOUT + 1)
