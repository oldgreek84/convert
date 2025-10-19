import importlib
import pkgutil

from abc import abstractmethod, ABC
from functools import wraps

registry = {}


def load_formats():
    """
    Dynamically import all submodules in this package (formats/*).
    This ensures all @register_format decorators are executed.
    """
    # Import all submodules in the formats package
    for _, module_name, _ in pkgutil.iter_modules(__path__):
        full_name = f"{__name__}.{module_name}"
        importlib.import_module(full_name)


def register_format(format_name):
    """Decorator to register a format class by name."""
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
    pass


class FormatTo(ABC):
    pass


class Format(ABC):
    def __init__(self, format_name):
        self.format_name = format_name

    @abstractmethod
    def allowed_formats(self) -> list:
        pass

    @abstractmethod
    def get_options(self):
        pass

    @abstractmethod
    def get_extension(self):
        pass
