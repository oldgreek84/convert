from __future__ import annotations

from typing import Protocol, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


class Worker(Protocol):
    """Protocol defining the interface for concurrent execution workers.

    This protocol establishes a standard interface for different concurrency
    implementations that can execute conversion operations in parallel or
    asynchronously. Workers allow the conversion process to run without
    blocking the user interface, providing better user experience.

    Workers handle the execution lifecycle:
    1. Execute a function with arguments in a separate execution context
    2. Track completion status of the operation
    3. Retrieve results when operation completes
    4. Handle errors that occur during execution

    Different implementations might use:
    - Threading for CPU-bound operations
    - Async/await for I/O-bound operations
    - Process pools for heavy computations
    - Remote execution for distributed processing

    The protocol ensures that different concurrency models can be used
    interchangeably depending on the specific requirements and constraints.
    """

    def is_completed(self) -> bool:
        """Check if the worker has finished executing.

        Returns the completion status of the currently running operation,
        allowing callers to poll for completion or implement waiting logic.

        Returns:
            True if the operation has finished (successfully or with error),
            False if still running or not started
        """
        raise NotImplementedError

    def get_result(self) -> Any:
        """Retrieve the result of the completed operation.

        Returns the return value from the executed function after the
        operation has completed successfully. The behavior is undefined
        if called before completion or if the operation failed.

        Returns:
            The return value from the executed function

        Raises:
            RuntimeError: If called before operation completion
            ExecutionError: If the operation failed during execution
        """
        raise NotImplementedError

    def execute(self, func: Callable, *args, **kwargs) -> None:
        """Execute a function concurrently with the provided arguments.

        Starts the execution of the specified function in a separate execution
        context (thread, process, coroutine, etc.) with the given arguments.
        The execution is asynchronous - this method returns immediately while
        the function runs in the background.

        Args:
            func: The function to execute concurrently
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Note:
            The worker should handle exceptions that occur during execution
            and make them available through the error handling mechanism.
        """
        raise NotImplementedError

    def set_error_handler(self, handler: Callable) -> None:
        """Set a callback function to handle execution errors.

        Registers a function that will be called if an exception occurs
        during the concurrent execution. This allows for proper error
        handling and user notification when operations fail.

        Args:
            handler: Callback function that accepts an exception as argument.
                    Will be called with the exception if execution fails.

        Example:
            >>> def handle_error(exception):
            ...     print(f"Operation failed: {exception}")
            >>> worker.set_error_handler(handle_error)
        """
        raise NotImplementedError
