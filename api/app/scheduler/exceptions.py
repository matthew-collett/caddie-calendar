class ProcessorError(Exception):
    pass


class AuthenticationFailedError(ProcessorError):
    def __init__(self, message="Failed to authenticate user credentials"):
        super().__init__(message)


class NoneAvailableError(ProcessorError):
    def __init__(self, message="No booking times are available for the requested date"):
        super().__init__(message)


class NoneDesiredError(ProcessorError):
    def __init__(self, message="No available time slots match the desired criteria"):
        super().__init__(message)


class AllFailedError(ProcessorError):
    def __init__(self, message="All booking attempts failed"):
        super().__init__(message)
