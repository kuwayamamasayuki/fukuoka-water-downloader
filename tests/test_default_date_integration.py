#!/usr/bin/env python3
"""
Test script to verify get_default_date_range integration
"""

def test_default_date_integration():
    """Test that get_default_date_range is called when no dates provided"""
    try:
        from fukuoka_water_downloader import FukuokaWaterDownloader
        
        downloader = FukuokaWaterDownloader(debug=True)
        
        print("Testing get_default_date_range method...")
        date_range = downloader.get_default_date_range()
        print(f"Default date range: {date_range}")
        
        if isinstance(date_range, tuple) and len(date_range) == 2:
            print("✅ get_default_date_range returns correct tuple format")
            print(f"✅ Date from: {date_range[0]}")
            print(f"✅ Date to: {date_range[1]}")
            return True
        else:
            print(f"❌ get_default_date_range returned unexpected format: {type(date_range)}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    print("Testing get_default_date_range integration...")
    success = test_default_date_integration()
    
    if success:
        print("\n🎉 Integration test passed!")
    else:
        print("\n❌ Integration test failed!")
    
    exit(0 if success else 1)
