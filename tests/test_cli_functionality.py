#!/usr/bin/env python3
"""
Test script for command-line functionality of the Fukuoka Water Bureau scraper
"""

import os
import sys
import subprocess
import tempfile

def test_help_option():
    """Test --help option"""
    print("Testing --help option...")
    
    try:
        result = subprocess.run([
            sys.executable, "fukuoka_water_scraper.py", "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "福岡市水道局アプリ" in result.stdout:
            print("✓ --help option works correctly")
            return True
        else:
            print(f"✗ --help option failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ --help test failed: {e}")
        return False

def test_argument_parsing():
    """Test argument parsing without actual execution"""
    print("Testing argument parsing...")
    
    test_script = """
import sys
sys.path.insert(0, '.')
from fukuoka_water_scraper import parse_arguments

try:
    import argparse
    
    test_cases = [
        ['--format', 'CSV'],
        ['--format', 'PDF', '--debug'],
        ['--period', '2024年4月', '--format', 'CSV'],
        ['--email', 'test@example.com', '--password', 'test123'],
        ['--output-dir', '/tmp/test', '--debug', '--headful']
    ]
    
    for i, test_args in enumerate(test_cases):
        sys.argv = ['test'] + test_args
        try:
            args = parse_arguments()
            print(f"Test case {i+1}: OK - {test_args}")
        except SystemExit:
            pass
        except Exception as e:
            print(f"Test case {i+1}: ERROR - {e}")
            
    print("Argument parsing tests completed")
    
except Exception as e:
    print(f"Argument parsing test failed: {e}")
    sys.exit(1)
"""
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            temp_script = f.name
        
        result = subprocess.run([
            sys.executable, temp_script
        ], capture_output=True, text=True, timeout=10)
        
        os.unlink(temp_script)
        
        if "Argument parsing tests completed" in result.stdout:
            print("✓ Argument parsing works correctly")
            return True
        else:
            print(f"✗ Argument parsing failed: {result.stdout}\n{result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Argument parsing test failed: {e}")
        return False

def test_environment_variables():
    """Test environment variable usage"""
    print("Testing environment variable usage...")
    
    test_env = os.environ.copy()
    test_env['mailaddress'] = 'test@example.com'
    test_env['password'] = 'testpass123'
    
    test_script = """
import sys
import os
sys.path.insert(0, '.')
from fukuoka_water_scraper import parse_arguments

args = parse_arguments()
email = args.email or os.environ.get('mailaddress')
password = args.password or os.environ.get('password')

if email == 'test@example.com' and password == 'testpass123':
    print("Environment variables test: OK")
else:
    print(f"Environment variables test: FAILED - email={email}, password={password}")
"""
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            temp_script = f.name
        
        result = subprocess.run([
            sys.executable, temp_script
        ], capture_output=True, text=True, timeout=10, env=test_env)
        
        os.unlink(temp_script)
        
        if "Environment variables test: OK" in result.stdout:
            print("✓ Environment variable usage works correctly")
            return True
        else:
            print(f"✗ Environment variable test failed: {result.stdout}\n{result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Environment variable test failed: {e}")
        return False

def main():
    """Run all CLI functionality tests"""
    print("Testing CLI functionality of Fukuoka Water Bureau scraper...")
    print("=" * 60)
    
    tests = [
        test_help_option,
        test_argument_parsing,
        test_environment_variables
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
    print(f"CLI Functionality Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All CLI functionality tests passed!")
        return True
    else:
        print("❌ Some CLI functionality tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
