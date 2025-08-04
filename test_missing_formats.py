#!/usr/bin/env python3
"""Test script for missing date formats reported by user"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fukuoka_water_downloader import FukuokaWaterDownloader

def test_missing_formats():
    """Test the specific formats that user reported as failing"""
    downloader = FukuokaWaterDownloader()
    
    print("Testing missing date formats:")
    
    # Formats that user reported as failing
    failing_formats = [
        "2024/1",    # Slash format
        "R6.1",      # R notation with dot
        "R6/1",      # R notation with slash
        "令和6年11月", # 2-digit month issue
        "2024.1",    # Dot format (also mentioned in README)
    ]
    
    # Formats that should work (for comparison)
    working_formats = [
        "令和7年5月",  # Single digit month that works
        "2024-1",     # Dash format that should work
        "令和6年1月",  # Single digit month
    ]
    
    print("\n=== Testing formats that user reported as failing ===")
    for date_format in failing_formats:
        try:
            result = downloader.convert_date_to_kenyin_format(date_format)
            print(f"  ✓ '{date_format}' -> '{result}'")
        except Exception as e:
            print(f"  ✗ '{date_format}' -> ERROR: {e}")
    
    print("\n=== Testing formats that should work (for comparison) ===")
    for date_format in working_formats:
        try:
            result = downloader.convert_date_to_kenyin_format(date_format)
            print(f"  ✓ '{date_format}' -> '{result}'")
        except Exception as e:
            print(f"  ✗ '{date_format}' -> ERROR: {e}")

if __name__ == "__main__":
    test_missing_formats()
