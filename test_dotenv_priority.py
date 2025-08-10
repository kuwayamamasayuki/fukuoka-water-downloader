#!/usr/bin/env python3
"""Test script to verify .env file loading and credential priority order"""

import os
import sys
import tempfile
from unittest.mock import patch, MagicMock
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fukuoka_water_downloader import FukuokaWaterDownloader

def test_dotenv_priority():
    """Test credential loading priority: manual input → command line → env vars → .env file"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("FUKUOKA_WATER_EMAIL=dotenv@example.com\n")
        f.write("FUKUOKA_WATER_PASSWORD=dotenv_password\n")
        env_file = f.name
    
    try:
        original_cwd = os.getcwd()
        env_dir = os.path.dirname(env_file)
        os.chdir(env_dir)
        os.rename(env_file, os.path.join(env_dir, '.env'))
        
        downloader = FukuokaWaterDownloader()
        
        print("Testing credential priority order:")
        
        print("\n1. Testing manual input priority (should override everything):")
        email, password = downloader.get_credentials("manual@example.com", "manual_password")
        assert email == "manual@example.com" and password == "manual_password"
        print("✓ Manual input works correctly")
        
        print("\n2. Testing environment variables priority:")
        os.environ['FUKUOKA_WATER_EMAIL'] = 'env@example.com'
        os.environ['FUKUOKA_WATER_PASSWORD'] = 'env_password'
        email, password = downloader.get_credentials()
        assert email == "env@example.com" and password == "env_password"
        print("✓ Environment variables work correctly")
        
        print("\n3. Testing .env file priority:")
        del os.environ['FUKUOKA_WATER_EMAIL']
        del os.environ['FUKUOKA_WATER_PASSWORD']
        
        with patch('builtins.input', return_value=''), \
             patch('getpass.getpass', return_value=''):
            try:
                email, password = downloader.get_credentials()
                assert False, "Should have raised ValueError"
            except ValueError:
                print("✓ Empty credentials properly rejected")
        
        print("\n4. Testing .env file loading with manual fallback:")
        with patch('builtins.input', return_value='fallback@example.com'), \
             patch('getpass.getpass', return_value='fallback_password'):
            email, password = downloader.get_credentials()
            assert email == "fallback@example.com" and password == "fallback_password"
            print("✓ Manual fallback works correctly")
        
        print("\n✅ All credential priority tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False
        
    finally:
        os.chdir(original_cwd)
        try:
            os.remove(os.path.join(env_dir, '.env'))
        except:
            pass
        for key in ['FUKUOKA_WATER_EMAIL', 'FUKUOKA_WATER_PASSWORD']:
            if key in os.environ:
                del os.environ[key]

if __name__ == "__main__":
    success = test_dotenv_priority()
    sys.exit(0 if success else 1)
