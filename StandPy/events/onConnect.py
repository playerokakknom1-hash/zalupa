from collections.abc import Callable
from StandPy import listeners

class OnConnect:
    def OnConnect(self) -> Callable:
        def decorator(func: Callable) -> Callable:
            self._dp.add_listener(listeners.OnConnect(func))
            return func
        return decorator
