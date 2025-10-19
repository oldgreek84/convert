import importlib
import pkgutil

from abc import abstractmethod, ABC
from functools import wraps

registry = {}


def load_formats():
    """Dynamically load all format modules and register their format classes.

    This function imports all Python modules in the formats package,
    ensuring that all @register_format decorators are executed and
    format classes are properly registered in the global registry.

    The function uses pkgutil to discover all modules in the package
    and imports them using importlib. This allows the format system
    to automatically detect and register new format implementations
    without requiring manual registration.

    Side Effects:
        - Imports all modules in the formats package
        - Executes @register_format decorators
        - Populates the global format registry
    """
    # Import all submodules in the formats package
    for _, module_name, _ in pkgutil.iter_modules(__path__):
        full_name = f"{__name__}.{module_name}"
        importlib.import_module(full_name)


def register_format(format_name):
    """Decorator to register a format class in the global format registry.

    This decorator registers format classes with their string identifiers,
    enabling dynamic format discovery and instantiation. The decorator
    wraps the class constructor to ensure proper initialization and
    name assignment.

    Args:
        format_name: String identifier for the format (e.g., 'fb2', 'mobi')

    Returns:
        Decorator function that registers the class and returns a wrapper

    Example:
        >>> @register_format('epub')
        ... class EpubFormat(Format):
        ...     def allowed_formats(self):
        ...         return ['mobi', 'pdf']
    """

    def my_decorator(aclass):
        @wraps(aclass)
        def wrapper(*args, **kwargs):
            instance = aclass(*args, **kwargs)
            if hasattr(instance, "name"):
                instance.name = format_name
            return instance

        registry[format_name] = wrapper
        print(f"Registered format: {format_name}")
        return wrapper

    return my_decorator


class FormatFrom(ABC):
    """Abstract base class for source format definitions.

    This class can be used to define format-specific behavior
    for source file formats in conversion operations.
    """

    pass


class FormatTo(ABC):
    """Abstract base class for target format definitions.

    This class can be used to define format-specific behavior
    for target file formats in conversion operations.
    """

    pass


class Format(ABC):
    """Abstract base class for format definitions and capabilities.

    This class defines the interface that all format implementations
    must follow. Format classes provide information about conversion
    capabilities, options, and file extensions for specific formats.

    Subclasses should implement all abstract methods to define:
    - Which formats this format can be converted to
    - Format-specific conversion options
    - File extension information

    Attributes:
        format_name: String identifier for this format
    """

    def __init__(self, format_name):
        """Initialize the format with its identifier.

        Args:
            format_name: String identifier for this format (e.g., 'fb2', 'mobi')
        """
        self.format_name = format_name

    @abstractmethod
    def allowed_formats(self) -> list:
        """Get the list of formats this format can be converted to.

        Returns:
            List of format identifiers that this format supports as conversion targets
        """
        pass

    @abstractmethod
    def get_options(self):
        """Get format-specific conversion options.

        Returns:
            Dictionary of options specific to this format's conversion process
        """
        pass

    @abstractmethod
    def get_extension(self):
        """Get the file extension for this format.

        Returns:
            String file extension including the dot (e.g., '.fb2', '.mobi')
        """
        pass
