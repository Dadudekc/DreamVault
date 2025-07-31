#!/usr/bin/env python3
"""
Test DreamVault Deployment System

Tests the deployment system components.
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dreamvault.deployment import (
    ModelManager,
    DeploymentConfig
)

def test_model_manager():
    """Test model manager functionality."""
    print("🧪 Testing Model Manager")
    print("=" * 30)
    
    try:
        # Initialize model manager
        model_manager = ModelManager("models")
        
        # Discover models
        models = model_manager.discover_models()
        print(f"✅ Discovered {len(models)} models")
        
        # List models
        model_info = model_manager.list_models()
        print(f"✅ Model info: {model_info.get('total_available', 0)} available, {model_info.get('total_loaded', 0)} loaded")
        
        # Test model loading (if models exist)
        if models:
            model_name = list(models.keys())[0]
            print(f"🔍 Testing model loading: {model_name}")
            
            success = model_manager.load_model(model_name)
            if success:
                print(f"✅ Model {model_name} loaded successfully")
                
                # Get model stats
                stats = model_manager.get_model_stats(model_name)
                print(f"✅ Model stats: {stats}")
                
                # Unload model
                model_manager.unload_model(model_name)
                print(f"✅ Model {model_name} unloaded")
            else:
                print(f"❌ Failed to load model {model_name}")
        else:
            print("ℹ️  No models found for testing")
        
        # Cleanup
        model_manager.cleanup()
        print("✅ Model manager cleanup completed")
        
    except Exception as e:
        print(f"❌ Model manager test error: {e}")

def test_deployment_config():
    """Test deployment configuration."""
    print("\n🧪 Testing Deployment Configuration")
    print("=" * 40)
    
    try:
        # Initialize config
        config = DeploymentConfig("test_deployment_config.json")
        
        # Test configuration methods
        print("✅ Configuration initialized")
        
        # Test get/set
        config.set("test.value", "test_data")
        value = config.get("test.value")
        print(f"✅ Get/Set test: {value}")
        
        # Test configuration sections
        api_config = config.get_api_config()
        web_config = config.get_web_config()
        model_config = config.get_model_config()
        
        print(f"✅ API config: {api_config.get('host')}:{api_config.get('port')}")
        print(f"✅ Web config: {web_config.get('host')}:{web_config.get('port')}")
        print(f"✅ Model config: {model_config.get('models_dir')}")
        
        # Test validation
        is_valid = config.validate_config()
        print(f"✅ Configuration validation: {is_valid}")
        
        # Test summary
        summary = config.get_summary()
        print(f"✅ Configuration summary: {len(summary)} sections")
        
        # Cleanup
        import os
        if os.path.exists("test_deployment_config.json"):
            os.remove("test_deployment_config.json")
        print("✅ Test configuration file cleaned up")
        
    except Exception as e:
        print(f"❌ Deployment config test error: {e}")

def test_deployment_integration():
    """Test deployment system integration."""
    print("\n🧪 Testing Deployment Integration")
    print("=" * 40)
    
    try:
        # Test configuration
        config = DeploymentConfig("test_integration_config.json")
        
        # Test model manager with config
        model_config = config.get_model_config()
        model_manager = ModelManager(model_config.get('models_dir', 'models'))
        
        # Test model discovery
        models = model_manager.discover_models()
        print(f"✅ Integration test: {len(models)} models discovered")
        
        # Test configuration with model manager
        api_config = config.get_api_config()
        web_config = config.get_web_config()
        
        print(f"✅ Integration test: API {api_config.get('host')}:{api_config.get('port')}")
        print(f"✅ Integration test: Web {web_config.get('host')}:{web_config.get('port')}")
        
        # Cleanup
        model_manager.cleanup()
        import os
        if os.path.exists("test_integration_config.json"):
            os.remove("test_integration_config.json")
        print("✅ Integration test cleanup completed")
        
    except Exception as e:
        print(f"❌ Integration test error: {e}")

def main():
    """Main test function."""
    print("🚀 DreamVault Deployment System Test")
    print("=" * 50)
    
    # Test model manager
    test_model_manager()
    
    # Test deployment configuration
    test_deployment_config()
    
    # Test integration
    test_deployment_integration()
    
    print(f"\n✅ All deployment system tests completed!")
    print(f"🚀 Ready to deploy: python run_deployment.py --show-config")

if __name__ == "__main__":
    main() 