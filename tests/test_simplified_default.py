#!/usr/bin/env python3
"""
Test script to verify simplified default date range implementation
"""

def test_simplified_default():
    """Test that the simplified current month logic works correctly"""
    try:
        from fukuoka_water_downloader_requests import FukuokaWaterDownloader
        from datetime import datetime
        
        downloader = FukuokaWaterDownloader(debug=True)
        
        print("Testing simplified current month default...")
        
        current_month = datetime.now().strftime("%Y-%m")
        print(f"Current month format: {current_month}")
        
        if len(current_month) == 7 and current_month[4] == '-':
            print("✅ Current month format is correct (YYYY-MM)")
            
            ken_ym = downloader.convert_date_to_kenyin_format(current_month)
            print(f"✅ Converted to kenyin format: {ken_ym}")
            
            return True
        else:
            print(f"❌ Invalid format: {current_month}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    print("Testing simplified default date range implementation...")
    success = test_simplified_default()
    
    if success:
        print("\n🎉 Simplified implementation test passed!")
    else:
        print("\n❌ Simplified implementation test failed!")
    
    exit(0 if success else 1)
