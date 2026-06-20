class StandPyRPCException(Exception):
    def __init__(self, exception):
        self.exception = exception
        self.code = getattr(exception, "code", 0)
        self.properties = getattr(exception, "properties", {})
        super().__init__(exception)
