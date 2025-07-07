#!/usr/bin/env python3
"""
Test script for enhanced date format parsing functionality
"""

import os
import sys
from fukuoka_water_scraper import FukuokaWaterScraper
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_date_conversion():
    """Test the enhanced date conversion functionality"""
    
    logger.info("Testing enhanced date format conversion...")
    logger.info("=" * 80)
    
    scraper = FukuokaWaterScraper()
    
    test_cases = [
        ("2024年1月", "令和　６年　１月検針分", "Standard Japanese format"),
        ("2024年01月", "令和　６年　１月検針分", "Standard Japanese format with zero-padded month"),
        ("2024/1", "令和　６年　１月検針分", "Western slash format"),
        ("2024/01", "令和　６年　１月検針分", "Western slash format with zero-padded month"),
        ("2024.1", "令和　６年　１月検針分", "Western dot format"),
        ("R6.1", "令和　６年　１月検針分", "Reiwa era shorthand with dot"),
        ("R6/1", "令和　６年　１月検針分", "Reiwa era shorthand with slash"),
        ("r6.1", "令和　６年　１月検針分", "Lowercase Reiwa era shorthand"),
        ("令和６年１月", "令和　６年　１月検針分", "Full Japanese era format"),
        ("令和6年1月", "令和　６年　１月検針分", "Mixed full-width/half-width Japanese era"),
        ("2025年3月", "令和　７年　３月検針分", "Year 2025 (Reiwa 7)"),
        ("R7.3", "令和　７年　３月検針分", "Reiwa 7 shorthand"),
        ("2024年11月", "令和　６年１１月検針分", "November (special spacing)"),
        ("R6.11", "令和　６年１１月検針分", "November in Reiwa shorthand"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for input_str, expected, description in test_cases:
        try:
            result = scraper.convert_western_to_japanese_era(input_str)
            
            if result == expected:
                logger.info(f"✓ PASS: {description}")
                logger.info(f"  Input: '{input_str}' → Output: '{result}'")
                passed += 1
            else:
                logger.error(f"✗ FAIL: {description}")
                logger.error(f"  Input: '{input_str}'")
                logger.error(f"  Expected: '{expected}'")
                logger.error(f"  Got: '{result}'")
        except Exception as e:
            logger.error(f"✗ ERROR: {description}")
            logger.error(f"  Input: '{input_str}' → Exception: {e}")
    
    logger.info("\n" + "=" * 80)
    logger.info(f"Date Conversion Test Results: {passed}/{total} tests passed")
    
    logger.info("\nTesting invalid date formats (should return None):")
    invalid_cases = [
        "invalid",
        "2018年1月",  # Before Reiwa era
        "2024年13月",  # Invalid month
        "R0.1",  # Invalid Reiwa year
        "2024/13",  # Invalid month
        "",  # Empty string
        None,  # None input
    ]
    
    invalid_passed = 0
    for invalid_input in invalid_cases:
        try:
            result = scraper.convert_western_to_japanese_era(invalid_input)
            if result is None:
                logger.info(f"✓ Correctly rejected: '{invalid_input}'")
                invalid_passed += 1
            else:
                logger.error(f"✗ Should have rejected: '{invalid_input}' → '{result}'")
        except Exception as e:
            logger.info(f"✓ Correctly rejected with exception: '{invalid_input}' → {e}")
            invalid_passed += 1
    
    logger.info(f"Invalid format handling: {invalid_passed}/{len(invalid_cases)} tests passed")
    
    overall_success = (passed == total) and (invalid_passed == len(invalid_cases))
    
    if overall_success:
        logger.info("\n🎉 All date conversion tests passed!")
    else:
        logger.error("\n❌ Some date conversion tests failed!")
    
    return overall_success

def test_real_scraper_with_formats():
    """Test the scraper with various date formats using real credentials"""
    
    email = os.environ.get('mailaddress')
    password = os.environ.get('password')
    
    if not email or not password:
        logger.error("Credentials not found in environment variables")
        return False
    
    logger.info("\n" + "=" * 80)
    logger.info("Testing real scraper with various date formats...")
    logger.info("=" * 80)
    
    test_formats = [
        ("2024/1", "Western slash format"),
        ("R6.1", "Reiwa era shorthand"),
        ("令和６年１月", "Full Japanese era format"),
    ]
    
    passed = 0
    total = len(test_formats)
    
    for date_format, description in test_formats:
        try:
            logger.info(f"\nTesting {description}: '{date_format}'")
            
            test_dir = f"/home/ubuntu/test_format_{date_format.replace('/', '_').replace('.', '_')}"
            scraper = FukuokaWaterScraper(headless=True, download_dir=test_dir, debug=True)
            
            result = scraper.run(
                email=email, 
                password=password, 
                period_from=date_format,
                period_to=None,
                format_type="CSV"
            )
            
            if result['success'] and result['files_downloaded']:
                logger.info(f"✓ PASS: {description} - Files downloaded successfully")
                passed += 1
            else:
                logger.error(f"✗ FAIL: {description} - {result.get('error_message', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"✗ ERROR: {description} - Exception: {e}")
    
    logger.info(f"\nReal scraper test results: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == "__main__":
    logger.info("Starting enhanced date format testing...")
    
    conversion_success = test_date_conversion()
    
    scraper_success = test_real_scraper_with_formats()
    
    logger.info("\n" + "=" * 80)
    logger.info("FINAL TEST SUMMARY:")
    logger.info("=" * 80)
    logger.info(f"Date Conversion Tests: {'✓ PASS' if conversion_success else '✗ FAIL'}")
    logger.info(f"Real Scraper Tests: {'✓ PASS' if scraper_success else '✗ FAIL'}")
    
    overall_success = conversion_success and scraper_success
    logger.info(f"\nOVERALL RESULT: {'✓ SUCCESS' if overall_success else '✗ FAILURE'}")
    
    if overall_success:
        logger.info("\n🎉 All enhanced date format tests passed!")
        logger.info("The scraper now supports multiple date input formats:")
        logger.info("  - 2024年1月 (Standard Japanese)")
        logger.info("  - 2024/1 (Western slash)")
        logger.info("  - R6.1 (Reiwa era shorthand)")
        logger.info("  - 令和６年１月 (Full Japanese era)")
    else:
        logger.error("\n❌ Some tests failed. Please check the logs above.")
    
    sys.exit(0 if overall_success else 1)
