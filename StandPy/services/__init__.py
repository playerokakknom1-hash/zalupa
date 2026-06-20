from .hello import HelloRemoteService
from .bolt import BoltRemoteService
from .handshake import HandshakeRemoteService
from .inventory import InventoryRemoteService
from .purchase import MarketplaceRemoteService
from .profile import PlayerRemoteService

class Services(
    HelloRemoteService,
    BoltRemoteService,
    HandshakeRemoteService,
    InventoryRemoteService,
    MarketplaceRemoteService,
    PlayerRemoteService
):
    def __init__(self):
        super().__init__()

__all__ = ["Services"]
