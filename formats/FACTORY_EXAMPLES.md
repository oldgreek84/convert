# Format Factory Pattern Examples

This document demonstrates how to use the format factory with different initialization parameters.

## Basic Usage (Simple Formats)

For formats without additional parameters:

```python
from formats import create_format

# Create simple format instances
fb2_format = create_format('fb2')
mobi_format = create_format('mobi')

# Use the format
print(fb2_format.allowed_formats())  # ['mobi', 'txt', 'pdf']
print(fb2_format.get_extension())     # '.fb2'
```

## Advanced Usage (Formats with Parameters)

For formats with additional initialization parameters:

```python
from formats import create_format

# Create PDF with default settings
pdf_default = create_format('pdf')
print(pdf_default.dpi)          # 150 (default)
print(pdf_default.color_mode)   # 'RGB' (default)
print(pdf_default.compression)  # True (default)

# Create PDF with custom settings
pdf_high_quality = create_format('pdf', dpi=300, color_mode='CMYK')
print(pdf_high_quality.dpi)         # 300
print(pdf_high_quality.color_mode)  # 'CMYK'
print(pdf_high_quality.compression) # True (still default)

# Create PDF with all custom settings
pdf_custom = create_format('pdf', dpi=600, color_mode='RGB', compression=False)
print(pdf_custom.get_options())
# Output: {'dpi': 600, 'color_mode': 'RGB', 'compression': False}
```

## Creating New Formats with Parameters

Here are examples of how to create new format classes with various parameter needs:

### Example 1: EPUB with Font Embedding

```python
from formats import Format, register_format

@register_format('epub')
class EpubFormat(Format):
    """EPUB format with font embedding options."""
    
    def __init__(
        self, 
        name: str,
        embed_fonts: bool = True,
        compression_level: int = 6
    ):
        super().__init__(name)
        self.embed_fonts = embed_fonts
        self.compression_level = compression_level
    
    def allowed_formats(self) -> list[str]:
        return ['mobi', 'pdf', 'fb2']
    
    def get_options(self) -> dict:
        return {
            'embed_fonts': self.embed_fonts,
            'compression_level': self.compression_level,
        }
    
    def get_extension(self) -> str:
        return '.epub'

# Usage:
epub_default = create_format('epub')
epub_custom = create_format('epub', embed_fonts=False, compression_level=9)
```

### Example 2: Image Format with Quality Settings

```python
@register_format('jpg')
class JpgFormat(Format):
    """JPEG format with quality and size parameters."""
    
    def __init__(
        self,
        name: str,
        quality: int = 85,
        max_width: int | None = None,
        max_height: int | None = None,
        progressive: bool = False
    ):
        super().__init__(name)
        self.quality = quality
        self.max_width = max_width
        self.max_height = max_height
        self.progressive = progressive
    
    def allowed_formats(self) -> list[str]:
        return ['png', 'webp', 'pdf']
    
    def get_options(self) -> dict:
        options = {'quality': self.quality, 'progressive': self.progressive}
        if self.max_width:
            options['max_width'] = self.max_width
        if self.max_height:
            options['max_height'] = self.max_height
        return options
    
    def get_extension(self) -> str:
        return '.jpg'

# Usage:
jpg_default = create_format('jpg')
jpg_thumbnail = create_format('jpg', quality=60, max_width=800, max_height=600)
jpg_web = create_format('jpg', quality=90, progressive=True)
```

### Example 3: Audio Format with Bitrate

```python
@register_format('mp3')
class Mp3Format(Format):
    """MP3 audio format with bitrate and quality settings."""
    
    def __init__(
        self,
        name: str,
        bitrate: int = 192,
        sample_rate: int = 44100,
        channels: int = 2,
        vbr: bool = False
    ):
        super().__init__(name)
        self.bitrate = bitrate
        self.sample_rate = sample_rate
        self.channels = channels
        self.vbr = vbr
    
    def allowed_formats(self) -> list[str]:
        return ['wav', 'flac', 'ogg', 'aac']
    
    def get_options(self) -> dict:
        return {
            'bitrate': self.bitrate,
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'vbr': self.vbr,
        }
    
    def get_extension(self) -> str:
        return '.mp3'

# Usage:
mp3_standard = create_format('mp3')
mp3_high_quality = create_format('mp3', bitrate=320, vbr=True)
mp3_mono = create_format('mp3', channels=1, bitrate=128)
```

## Dynamic Configuration from User Input

You can also build parameters dynamically from configuration files or user input:

```python
from formats import create_format

def create_format_from_config(format_name: str, config_dict: dict):
    """Create format from configuration dictionary."""
    return create_format(format_name, **config_dict)

# From config file
config = {
    'dpi': 300,
    'color_mode': 'CMYK',
    'compression': True
}
pdf = create_format_from_config('pdf', config)

# From user input
user_settings = get_user_preferences()  # Returns dict
format_instance = create_format('pdf', **user_settings)
```

## Best Practices

1. **Use sensible defaults**: All additional parameters should have default values
2. **Document parameters**: Use docstrings to explain what each parameter does
3. **Type hints**: Always add type hints for better IDE support and validation
4. **Validate inputs**: Consider adding validation in `__init__` for invalid values
5. **Keep it simple**: Only add parameters that truly vary between use cases

## Validation Example

```python
@register_format('video')
class VideoFormat(Format):
    """Video format with validation."""
    
    def __init__(
        self,
        name: str,
        fps: int = 30,
        resolution: str = '1920x1080'
    ):
        super().__init__(name)
        
        # Validate FPS
        if fps <= 0 or fps > 120:
            raise ValueError(f"FPS must be between 1 and 120, got {fps}")
        
        # Validate resolution format
        if not self._is_valid_resolution(resolution):
            raise ValueError(f"Invalid resolution format: {resolution}")
        
        self.fps = fps
        self.resolution = resolution
    
    @staticmethod
    def _is_valid_resolution(res: str) -> bool:
        """Check if resolution string is valid (e.g., '1920x1080')."""
        try:
            width, height = res.split('x')
            return int(width) > 0 and int(height) > 0
        except (ValueError, AttributeError):
            return False
    
    def allowed_formats(self) -> list[str]:
        return ['mp4', 'avi', 'mkv']
    
    def get_options(self) -> dict:
        return {'fps': self.fps, 'resolution': self.resolution}
    
    def get_extension(self) -> str:
        return '.mp4'

# Usage - with validation
try:
    video = create_format('video', fps=200)  # Raises ValueError
except ValueError as e:
    print(f"Invalid settings: {e}")
```
