#!/usr/bin/env python3
"""
Test script to verify current month default date range implementation
"""

def test_current_month_default():
    """Test that get_default_date_range returns current month when web scraping fails"""
    try:
        from fukuoka_water_downloader_requests import FukuokaWaterDownloader
        from datetime import datetime
        
        downloader = FukuokaWaterDownloader(debug=True)
        
        print("Testing current month default date range...")
        date_range = downloader.get_default_date_range()
        print(f"Returned date range: {date_range}")
        
        today = datetime.now()
        first_day_of_month = today.replace(day=1)
        if today.month == 12:
            from datetime import timedelta
            last_day_of_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            from datetime import timedelta
            last_day_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        
        expected_start = first_day_of_month.strftime("%Y-%m-%d")
        expected_end = last_day_of_month.strftime("%Y-%m-%d")
        
        print(f"Expected date range: {expected_start} to {expected_end}")
        
        if isinstance(date_range, tuple) and len(date_range) == 2:
            actual_start, actual_end = date_range
            if actual_start == expected_start and actual_end == expected_end:
                print("✅ Current month default date range is correct")
                return True
            else:
                print(f"❌ Date range mismatch. Got: {actual_start} to {actual_end}")
                return False
        else:
            print(f"❌ Invalid return format: {type(date_range)}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    print("Testing current month default date range implementation...")
    success = test_current_month_default()
    
    if success:
        print("\n🎉 Current month default test passed!")
    else:
        print("\n❌ Current month default test failed!")
    
    exit(0 if success else 1)
