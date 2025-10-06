class ProcessorError(Exception):
    pass


class SessionError(ProcessorError):
    def __init__(
        self, message="Unable to authenticate - please verify your login credentials"
    ):
        super().__init__(message)


class NoTimesError(ProcessorError):
    def __init__(self, message="No tee times are available for your selected date"):
        super().__init__(message)


class NoSlotsError(ProcessorError):
    def __init__(self, message="No available tee times match your booking preferences"):
        super().__init__(message)


class AllReserveFailed(ProcessorError):
    def __init__(
        self,
        message="Unable to secure any available tee times - all attempts were unsuccessful",
    ):
        super().__init__(message)
