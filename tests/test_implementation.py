#!/usr/bin/env python3
"""
Test script to verify the implementation changes
"""

def test_imports():
    """Test that all imports work correctly"""
    try:
        from fukuoka_water_downloader import FukuokaWaterDownloader
        from bs4 import BeautifulSoup
        from typing import Tuple, Optional
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_method_signatures():
    """Test that method signatures are correct"""
    try:
        from fukuoka_water_downloader import FukuokaWaterDownloader
        downloader = FukuokaWaterDownloader(debug=True)
        
        date_range = downloader.get_default_date_range()
        if isinstance(date_range, tuple) and len(date_range) == 2:
            print("✅ get_default_date_range returns correct tuple format")
        else:
            print(f"❌ get_default_date_range returned: {type(date_range)}")
            return False
            
        print("✅ Method signatures are correct")
        return True
    except Exception as e:
        print(f"❌ Method signature error: {e}")
        return False

if __name__ == "__main__":
    print("Testing implementation changes...")
    
    success = True
    success &= test_imports()
    success &= test_method_signatures()
    
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    exit(0 if success else 1)
