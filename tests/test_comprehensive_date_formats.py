#!/usr/bin/env python3
"""Comprehensive test for all documented date formats"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fukuoka_water_downloader import FukuokaWaterDownloader

def test_all_documented_formats():
    """Test all date formats documented in README.md"""
    downloader = FukuokaWaterDownloader()
    
    test_cases = [
        ("令和7年5月", "令和　７年　５月検針分"),
        ("令和6年11月", "令和　６年１１月検針分"),
        ("2024-1", "令和　６年　１月検針分"),
        ("2024年1月", "令和　６年　１月検針分"),
        
        ("2024/1", "令和　６年　１月検針分"),
        ("2024.1", "令和　６年　１月検針分"),
        ("R6.1", "令和　６年　１月検針分"),
        ("R6/1", "令和　６年　１月検針分"),
        
        ("2025/12", "令和　７年１２月検針分"),
        ("R7.12", "令和　７年１２月検針分"),
        ("2019/4", "令和　１年　４月検針分"),
    ]
    
    print("Testing all documented date formats:")
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
    success = test_all_documented_formats()
    print(f"\nComprehensive date format test {'PASSED' if success else 'FAILED'}!")
    sys.exit(0 if success else 1)
