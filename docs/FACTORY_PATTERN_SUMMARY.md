# Format Factory Pattern - Summary

## Problem Solved

Your original decorator was registering a **function wrapper** instead of the **class itself**, causing type confusion and making it impossible to use class methods properly.

## Solution Implemented

### 1. Clean Decorator Pattern

```python
def register_format(format_name: str):
    """Simple decorator that registers the class and returns it unchanged."""
    def decorator(format_class):
        registry[format_name] = format_class  # Register the CLASS
        return format_class                    # Return the CLASS
    return decorator
```

**Key changes:**
- ❌ Removed wrapper function that was causing confusion
- ❌ Removed duplicate `@resg` decorator
- ✅ Direct class registration
- ✅ Returns the class unchanged

### 2. Factory Function with **kwargs

```python
def create_format(name: str, **kwargs) -> Format | None:
    """Factory: Create format instance with optional parameters.
    
    Examples:
        >>> fb2 = create_format('fb2')                    # Simple format
        >>> pdf = create_format('pdf', dpi=300)           # With parameters
        >>> pdf = create_format('pdf', dpi=600, color_mode='CMYK')
    """
    format_class = registry.get(name)
    if format_class:
        return format_class(name, **kwargs)
    return None
```

**Benefits:**
- ✅ Handles simple formats (no extra params)
- ✅ Handles complex formats (with extra params)
- ✅ All extra params are optional with defaults
- ✅ Type-safe and clear

## Usage Examples

### Simple Format (No Extra Parameters)

```python
@register_format('fb2')
class Fb2Format(Format):
    def __init__(self, name: str):
        super().__init__(name)
    
    def allowed_formats(self) -> list[str]:
        return ['mobi', 'txt', 'pdf']

# Usage
fb2 = create_format('fb2')
```

### Complex Format (With Extra Parameters)

```python
@register_format('pdf')
class PdfFormat(Format):
    def __init__(
        self, 
        name: str, 
        dpi: int = 150,           # Optional with default
        color_mode: str = 'RGB',  # Optional with default
        compression: bool = True  # Optional with default
    ):
        super().__init__(name)
        self.dpi = dpi
        self.color_mode = color_mode
        self.compression = compression
    
    def allowed_formats(self) -> list[str]:
        return ['fb2', 'mobi', 'txt']
    
    def get_options(self) -> dict:
        return {
            'dpi': self.dpi,
            'color_mode': self.color_mode,
            'compression': self.compression,
        }

# Usage - all variations work
pdf1 = create_format('pdf')                           # All defaults
pdf2 = create_format('pdf', dpi=300)                  # Override one
pdf3 = create_format('pdf', dpi=600, color_mode='CMYK')  # Override multiple
```

### Future Example: EPUB with Font Embedding

```python
@register_format('epub')
class EpubFormat(Format):
    def __init__(
        self,
        name: str,
        embed_fonts: bool = True,
        compression_level: int = 6,
        include_toc: bool = True
    ):
        super().__init__(name)
        self.embed_fonts = embed_fonts
        self.compression_level = compression_level
        self.include_toc = include_toc

# Usage
epub_default = create_format('epub')
epub_custom = create_format('epub', embed_fonts=False, compression_level=9)
```

## Key Principles for Future Formats

1. **First parameter is always `name: str`** - passed by factory
2. **All additional parameters must have defaults** - for flexibility
3. **Use type hints** - for IDE support and validation
4. **Document parameters** - in docstrings
5. **Validation in `__init__`** - catch bad values early

## Migration Guide

### Before (Broken)
```python
format_class = formats.get_format('fb2')  # Returns CLASS
format_class.allowed_formats()             # ERROR: calling instance method on class
```

### After (Working)
```python
# Option 1: Use factory (recommended)
format_instance = formats.create_format('fb2')
format_instance.allowed_formats()  # ✅ Works

# Option 2: Manual instantiation
format_class = formats.get_format('fb2')
format_instance = format_class('fb2')
format_instance.allowed_formats()  # ✅ Works
```

## Files Changed

1. **formats/__init__.py**
   - Simplified `register_format()` decorator
   - Added `create_format()` factory function
   - Fixed return type hints on abstract methods
   - Removed unnecessary `resg()` and wrapper functions

2. **formats/formats.py**
   - Removed `@resg` decorator
   - Fixed `__init__` to use parameter instead of hardcoded value
   - Added type hints
   - Added PDF format as example with parameters
   - Fixed method names (`get_option` → `get_options`)

3. **Documentation**
   - Created FACTORY_EXAMPLES.md with comprehensive examples
   - Created this summary document

## Testing

Run the demonstration:
```bash
uv run python test_factory_demo.py
```

This shows:
- Simple formats working
- Complex formats with defaults
- Complex formats with custom parameters
- Dynamic configuration from dictionaries
- Error handling for unknown formats
