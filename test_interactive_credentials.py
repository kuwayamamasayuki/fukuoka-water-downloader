#!/usr/bin/env python3
"""
Test script for interactive credential input functionality
"""

import os
import sys
import subprocess
import tempfile
import time

def test_interactive_input():
    """Test interactive credential input when no credentials are provided"""
    print("Testing interactive credential input...")
    
    test_script = """
import sys
import os
import subprocess
from unittest.mock import patch

env = os.environ.copy()
if 'mailaddress' in env:
    del env['mailaddress']
if 'password' in env:
    del env['password']

with patch('builtins.input', return_value='test@example.com'):
    with patch('getpass.getpass', return_value='testpassword123'):
        sys.path.insert(0, '.')
        from fukuoka_water_scraper import parse_arguments
        
        print("Interactive input test: Mocked input successful")
"""
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            temp_script = f.name
        
        result = subprocess.run([
            sys.executable, temp_script
        ], capture_output=True, text=True, timeout=10)
        
        os.unlink(temp_script)
        
        if "Interactive input test: Mocked input successful" in result.stdout:
            print("✓ Interactive input test passed")
            return True
        else:
            print(f"✗ Interactive input test failed: {result.stdout}\n{result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Interactive input test failed: {e}")
        return False

def test_cli_credentials():
    """Test CLI credential arguments"""
    print("Testing CLI credential arguments...")
    
    try:
        result = subprocess.run([
            sys.executable, "fukuoka_water_scraper.py", 
            "--email", "test@example.com",
            "--password", "testpass123",
            "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "福岡市水道局アプリ" in result.stdout:
            print("✓ CLI credentials test passed")
            return True
        else:
            print(f"✗ CLI credentials test failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ CLI credentials test failed: {e}")
        return False

def test_environment_credentials():
    """Test environment variable credentials"""
    print("Testing environment variable credentials...")
    
    test_env = os.environ.copy()
    test_env['mailaddress'] = 'test@example.com'
    test_env['password'] = 'testpass123'
    
    try:
        result = subprocess.run([
            sys.executable, "fukuoka_water_scraper.py", "--help"
        ], capture_output=True, text=True, timeout=10, env=test_env)
        
        if result.returncode == 0 and "福岡市水道局アプリ" in result.stdout:
            print("✓ Environment credentials test passed")
            return True
        else:
            print(f"✗ Environment credentials test failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Environment credentials test failed: {e}")
        return False

def main():
    """Run all credential input tests"""
    print("Testing credential input functionality...")
    print("=" * 60)
    
    tests = [
        test_interactive_input,
        test_cli_credentials,
        test_environment_credentials
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            print()
        except Exception as e:
            print(f"✗ Test {test_func.__name__} failed with exception: {e}")
            print()
    
    print("=" * 60)
    print(f"Credential Input Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All credential input tests passed!")
        return True
    else:
        print("❌ Some credential input tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
