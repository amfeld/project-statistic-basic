#!/usr/bin/env python3
"""
Clean Odoo 18 Enterprise PO file by removing incompatible translation blocks.

This script removes translation blocks with the following headers:
- #: view string
- #: wizard
- #: sum label
- #: pivot view string
- #: graph view string

These block types are incompatible with Odoo 18 Enterprise and cause
module installation failures or runtime errors.
"""

import re
import sys
from pathlib import Path


INCOMPATIBLE_HEADERS = [
    'view string',
    'wizard',
    'sum label',
    'pivot view string',
    'graph view string',
]


def clean_po_file(input_path: str, output_path: str = None, backup: bool = True) -> dict:
    """
    Clean PO file by removing incompatible translation blocks.

    Args:
        input_path: Path to the PO file to clean
        output_path: Path for cleaned file (defaults to same as input)
        backup: Whether to create a backup file (default: True)

    Returns:
        Dictionary with statistics about removed blocks
    """
    input_file = Path(input_path)

    if not input_file.exists():
        raise FileNotFoundError(f"PO file not found: {input_path}")

    if output_path is None:
        output_path = input_path

    if backup and output_path == input_path:
        backup_path = input_file.with_suffix('.po.backup')
        input_file.rename(backup_path)
        print(f"✓ Backup created: {backup_path}")
        input_file = backup_path

    content = input_file.read_text(encoding='utf-8')

    pattern = r'(?ms)^#\. module: [^\n]+\n#:\s*(?:' + '|'.join(
        re.escape(header) for header in INCOMPATIBLE_HEADERS
    ) + r')\nmsgid\s+"(?:[^"]|\\")*"\nmsgstr\s+"(?:[^"]|\\")*"\n'

    removed_blocks = []

    def collect_removed(match):
        removed_blocks.append(match.group(0))
        return ''

    cleaned_content = re.sub(pattern, collect_removed, content)

    Path(output_path).write_text(cleaned_content, encoding='utf-8')

    stats = {
        'total_removed': len(removed_blocks),
        'by_type': {},
        'file_size_before': len(content),
        'file_size_after': len(cleaned_content),
    }

    for block in removed_blocks:
        for header in INCOMPATIBLE_HEADERS:
            if f'#: {header}\n' in block:
                stats['by_type'][header] = stats['by_type'].get(header, 0) + 1
                break

    return stats


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        script_name = Path(__file__).name
        print(f"Usage: python3 {script_name} <po_file_path> [output_path]")
        print("\nExample:")
        print(f"  python3 {script_name} i18n/de.po")
        print(f"  python3 {script_name} i18n/de.po i18n/de_cleaned.po")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"\n{'='*60}")
    print("Odoo 18 Enterprise PO File Cleaner")
    print(f"{'='*60}\n")

    try:
        stats = clean_po_file(input_path, output_path, backup=True)

        print(f"✓ Successfully cleaned PO file: {output_path or input_path}")
        print(f"\n{'='*60}")
        print("Statistics:")
        print(f"{'='*60}")
        print(f"Total blocks removed: {stats['total_removed']}")
        print(f"\nRemoved by type:")
        for header, count in sorted(stats['by_type'].items()):
            print(f"  - {header}: {count} blocks")
        print(f"\nFile size:")
        print(f"  - Before: {stats['file_size_before']:,} bytes")
        print(f"  - After:  {stats['file_size_after']:,} bytes")
        print(f"  - Saved:  {stats['file_size_before'] - stats['file_size_after']:,} bytes")
        print(f"\n{'='*60}")
        print("\nNext steps:")
        print("1. Restart your Odoo server")
        print("2. Upgrade the module")
        print("3. Verify translations are working correctly")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
