class ProcessorError(Exception):
    """Exception raised when processor operations fail.

    This exception is thrown when conversion processing encounters errors
    such as invalid files, processing failures, external tool errors,
    or communication issues with processing services.

    Attributes:
        message: Descriptive error message about the processing failure.
    """
