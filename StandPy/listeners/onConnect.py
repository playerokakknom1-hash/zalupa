from StandPy.listener import Listener
from StandPy.enums.events import BaseEvent

class OnConnect(Listener):
    event = BaseEvent.CONNECT
