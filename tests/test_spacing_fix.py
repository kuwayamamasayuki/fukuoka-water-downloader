#!/usr/bin/env python3
"""Test script to verify correct spacing for 2-digit months"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fukuoka_water_downloader import FukuokaWaterDownloader

def test_spacing_fix():
    """Test that 2-digit months have correct spacing"""
    downloader = FukuokaWaterDownloader()
    
    test_cases = [
        ("令和6年11月", "令和６年１１月検針分"),
        ("令和7年5月", "令和　７年　５月検針分"),
        ("2024/11", "令和６年１１月検針分"),
        ("2024/5", "令和　６年　５月検針分"),
        ("R6.11", "令和６年１１月検針分"),
        ("R6.5", "令和　６年　５月検針分"),
        ("2025/12", "令和７年１２月検針分"),
        ("2025/1", "令和　７年　１月検針分"),
    ]
    
    print("Testing correct spacing for 2-digit months:")
    all_passed = True
    
    for input_date, expected in test_cases:
        try:
            result = downloader.convert_date_to_kenyin_format(input_date)
            status = "✓" if result == expected else "✗"
            if result != expected:
                all_passed = False
                print(f"  {status} '{input_date}' -> '{result}' (expected: '{expected}')")
            else:
                print(f"  {status} '{input_date}' -> '{result}'")
        except Exception as e:
            print(f"  ✗ '{input_date}' -> ERROR: {e}")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    success = test_spacing_fix()
    print(f"\nSpacing fix test {'PASSED' if success else 'FAILED'}!")
    sys.exit(0 if success else 1)
