from StandPy.types.update import Update
from StandPy.enums.events import BaseEvent

class Connected(Update):
    event = BaseEvent.CONNECT
