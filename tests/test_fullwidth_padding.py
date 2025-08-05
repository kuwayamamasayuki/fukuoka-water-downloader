#!/usr/bin/env python3
"""Test script to verify 2-digit full-width padding for year and month"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fukuoka_water_downloader import FukuokaWaterDownloader

def test_fullwidth_padding():
    """Test that year and month are always 2 full-width characters with padding"""
    downloader = FukuokaWaterDownloader()
    
    test_cases = [
        ("令和7年5月", "令和　７年　５月検針分"),
        ("令和6年1月", "令和　６年　１月検針分"),
        ("2024/1", "令和　６年　１月検針分"),
        ("2024.5", "令和　６年　５月検針分"),
        ("R6.1", "令和　６年　１月検針分"),
        ("R6/5", "令和　６年　５月検針分"),
        
        ("令和6年11月", "令和　６年１１月検針分"),
        ("令和10年12月", "令和１０年１２月検針分"),
        ("2024/11", "令和　６年１１月検針分"),
        ("2024.12", "令和　６年１２月検針分"),
        ("R6.11", "令和　６年１１月検針分"),
        ("R10/12", "令和１０年１２月検針分"),
        
        ("令和7年11月", "令和　７年１１月検針分"),  # single digit year, double digit month
        ("令和10年5月", "令和１０年　５月検針分"),   # double digit year, single digit month
        
        ("平成31年4月", "平成３１年　４月検針分"),
        ("2018/12", "平成３０年１２月検針分"),
        ("2019/4", "令和　１年　４月検針分"),
    ]
    
    print("Testing 2-digit full-width padding for year and month:")
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
    success = test_fullwidth_padding()
    print(f"\nFull-width padding test {'PASSED' if success else 'FAILED'}!")
    sys.exit(0 if success else 1)
