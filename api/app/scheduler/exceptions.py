class ProcessorError(Exception):
    pass


class AuthenticationFailedError(ProcessorError):
    def __init__(self, message="Failed to authenticate"):
        super().__init__(message)


class NoneAvailableError(ProcessorError):
    def __init__(self, message="Could not find any times to book"):
        super().__init__(message)


class NoneDesiredError(ProcessorError):
    def __init__(self, message="Could not find any available times to book"):
        super().__init__(message)


class AllFailedError(ProcessorError):
    def __init__(self, message="All booking attempts failed"):
        super().__init__(message)
