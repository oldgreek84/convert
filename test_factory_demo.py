"""Demonstration of the format factory pattern with different parameters."""

from formats import create_format, load_formats

def main():
    # Load all format modules
    load_formats()
    
    print("=" * 80)
    print("FORMAT FACTORY PATTERN DEMONSTRATION")
    print("=" * 80)
    
    # 1. Simple formats (no extra parameters)
    print("\n1. Simple Formats (default initialization):")
    print("-" * 80)
    
    fb2 = create_format('fb2')
    print(f"FB2 Format: {fb2}")
    print(f"  - Name: {fb2.format_name}")
    print(f"  - Extension: {fb2.get_extension()}")
    print(f"  - Can convert to: {fb2.allowed_formats()}")
    print(f"  - Options: {fb2.get_options()}")
    
    mobi = create_format('mobi')
    print(f"\nMOBI Format: {mobi}")
    print(f"  - Name: {mobi.format_name}")
    print(f"  - Extension: {mobi.get_extension()}")
    print(f"  - Can convert to: {mobi.allowed_formats()}")
    
    # 2. Format with additional parameters (using defaults)
    print("\n\n2. PDF Format with Default Parameters:")
    print("-" * 80)
    
    pdf_default = create_format('pdf')
    print(f"PDF Format (default): {pdf_default}")
    print(f"  - Name: {pdf_default.format_name}")
    print(f"  - Extension: {pdf_default.get_extension()}")
    print(f"  - DPI: {pdf_default.dpi}")
    print(f"  - Color Mode: {pdf_default.color_mode}")
    print(f"  - Compression: {pdf_default.compression}")
    print(f"  - Options: {pdf_default.get_options()}")
    
    # 3. Format with custom parameters
    print("\n\n3. PDF Format with Custom Parameters:")
    print("-" * 80)
    
    pdf_hq = create_format('pdf', dpi=300, color_mode='CMYK')
    print(f"PDF Format (high quality): {pdf_hq}")
    print(f"  - Name: {pdf_hq.format_name}")
    print(f"  - DPI: {pdf_hq.dpi}")
    print(f"  - Color Mode: {pdf_hq.color_mode}")
    print(f"  - Compression: {pdf_hq.compression}")
    print(f"  - Options: {pdf_hq.get_options()}")
    
    pdf_custom = create_format('pdf', dpi=600, color_mode='RGB', compression=False)
    print(f"\nPDF Format (custom all params): {pdf_custom}")
    print(f"  - DPI: {pdf_custom.dpi}")
    print(f"  - Color Mode: {pdf_custom.color_mode}")
    print(f"  - Compression: {pdf_custom.compression}")
    print(f"  - Options: {pdf_custom.get_options()}")
    
    # 4. Dynamic configuration
    print("\n\n4. Dynamic Configuration from Dictionary:")
    print("-" * 80)
    
    config = {
        'dpi': 450,
        'color_mode': 'CMYK',
        'compression': True
    }
    pdf_from_config = create_format('pdf', **config)
    print(f"PDF from config {config}:")
    print(f"  - Options: {pdf_from_config.get_options()}")
    
    # 5. Non-existent format
    print("\n\n5. Error Handling:")
    print("-" * 80)
    
    unknown = create_format('unknown_format')
    print(f"Unknown format result: {unknown}")
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
