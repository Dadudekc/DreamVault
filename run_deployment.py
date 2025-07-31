#!/usr/bin/env python3
"""
DreamVault Agent Deployment Script

Deploys trained AI agents with API server and web interface.
"""

import argparse
import logging
import sys
import signal
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dreamvault.deployment import (
    AgentAPIServer,
    AgentWebInterface,
    ModelManager,
    DeploymentConfig
)

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('deployment.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def start_deployment(config_file: str = "configs/deployment.json", api_only: bool = False, web_only: bool = False):
    """
    Start the deployment system.
    
    Args:
        config_file: Path to deployment configuration
        api_only: Start only API server
        web_only: Start only web interface
    """
    print("🚀 DreamVault Agent Deployment")
    print("=" * 40)
    
    # Load configuration
    try:
        config = DeploymentConfig(config_file)
        if not config.validate_config():
            print("❌ Configuration validation failed")
            return False
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False
    
    # Get configuration sections
    api_config = config.get_api_config()
    web_config = config.get_web_config()
    model_config = config.get_model_config()
    
    print(f"📋 Configuration loaded: {config_file}")
    print(f"🔧 API Server: {api_config.get('host')}:{api_config.get('port')}")
    print(f"🌐 Web Interface: {web_config.get('host')}:{web_config.get('port')}")
    print(f"🤖 Models Directory: {model_config.get('models_dir')}")
    
    # Initialize components
    api_server = None
    web_interface = None
    
    try:
        # Start API server (unless web_only mode)
        if not web_only:
            print(f"\n🔧 Starting API Server...")
            api_server = AgentAPIServer(
                models_dir=model_config.get('models_dir', 'models'),
                host=api_config.get('host', '0.0.0.0'),
                port=api_config.get('port', 8000)
            )
            api_server.start(debug=api_config.get('debug', False))
            print(f"✅ API Server started: http://{api_config.get('host')}:{api_config.get('port')}")
        
        # Start web interface (unless api_only mode)
        if not api_only:
            print(f"\n🌐 Starting Web Interface...")
            web_interface = AgentWebInterface(
                api_url=f"http://{api_config.get('host', 'localhost')}:{api_config.get('port', 8000)}",
                host=web_config.get('host', '0.0.0.0'),
                port=web_config.get('port', 8080)
            )
            web_interface.start(open_browser=web_config.get('auto_open_browser', True))
            print(f"✅ Web Interface started: http://{web_config.get('host')}:{web_config.get('port')}")
        
        # Show status
        print(f"\n🎯 Deployment Status:")
        if api_server:
            print(f"   API Server: {'✅ Running' if api_server.is_running() else '❌ Stopped'}")
        if web_interface:
            print(f"   Web Interface: {'✅ Running' if web_interface.is_running() else '❌ Stopped'}")
        
        print(f"\n📚 Available Endpoints:")
        if api_server:
            print(f"   Health Check: http://{api_config.get('host')}:{api_config.get('port')}/health")
            print(f"   Models List: http://{api_config.get('host')}:{api_config.get('port')}/models")
            print(f"   Conversation: http://{api_config.get('host')}:{api_config.get('port')}/conversation")
            print(f"   Summarization: http://{api_config.get('host')}:{api_config.get('port')}/summarize")
            print(f"   Q&A: http://{api_config.get('host')}:{api_config.get('port')}/qa")
            print(f"   Instructions: http://{api_config.get('host')}:{api_config.get('port')}/instruction")
            print(f"   Embeddings: http://{api_config.get('host')}:{api_config.get('port')}/embed")
        
        if web_interface:
            print(f"   Web UI: http://{web_config.get('host')}:{web_config.get('port')}")
        
        print(f"\n💡 Usage Examples:")
        print(f"   # Test conversation agent")
        print(f"   curl -X POST http://localhost:8000/conversation \\")
        print(f"     -H 'Content-Type: application/json' \\")
        print(f"     -d '{{\"input\": \"Hello, how are you?\"}}'")
        
        print(f"\n   # Test summarization agent")
        print(f"   curl -X POST http://localhost:8000/summarize \\")
        print(f"     -H 'Content-Type: application/json' \\")
        print(f"     -d '{{\"text\": \"Your text to summarize here...\"}}'")
        
        print(f"\n🔄 Press Ctrl+C to stop deployment")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\n🛑 Stopping deployment...")
        
        if web_interface:
            web_interface.stop()
            print("✅ Web Interface stopped")
        
        if api_server:
            api_server.stop()
            print("✅ API Server stopped")
        
        print("✅ Deployment stopped")
        return True
        
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        
        if web_interface:
            web_interface.stop()
        
        if api_server:
            api_server.stop()
        
        return False

def show_config(config_file: str):
    """Show deployment configuration."""
    try:
        config = DeploymentConfig(config_file)
        summary = config.get_summary()
        
        print("📋 DreamVault Deployment Configuration")
        print("=" * 50)
        
        print(f"\n🔧 API Server:")
        print(f"   Host: {summary['api_server']['host']}")
        print(f"   Port: {summary['api_server']['port']}")
        print(f"   Debug: {summary['api_server']['debug']}")
        
        print(f"\n🌐 Web Interface:")
        print(f"   Host: {summary['web_interface']['host']}")
        print(f"   Port: {summary['web_interface']['port']}")
        print(f"   Auto-open Browser: {summary['web_interface']['auto_open_browser']}")
        
        print(f"\n🤖 Model Manager:")
        print(f"   Models Directory: {summary['model_manager']['models_dir']}")
        print(f"   Auto-load Models: {summary['model_manager']['auto_load_models']}")
        print(f"   Max Models in Memory: {summary['model_manager']['max_models_in_memory']}")
        
        print(f"\n🔒 Security:")
        print(f"   API Key Required: {summary['security']['api_key_required']}")
        print(f"   Allowed Origins: {summary['security']['allowed_origins']}")
        
        print(f"\n⚡ Performance:")
        print(f"   Enable Caching: {summary['performance']['enable_caching']}")
        print(f"   Max Concurrent Requests: {summary['performance']['max_concurrent_requests']}")
        
    except Exception as e:
        print(f"❌ Error showing configuration: {e}")

def test_deployment(config_file: str):
    """Test deployment endpoints."""
    try:
        config = DeploymentConfig(config_file)
        api_config = config.get_api_config()
        
        import requests
        
        base_url = f"http://{api_config.get('host', 'localhost')}:{api_config.get('port', 8000)}"
        
        print("🧪 Testing DreamVault Deployment")
        print("=" * 40)
        
        # Test health endpoint
        print(f"\n🔍 Testing health endpoint...")
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Health check error: {e}")
        
        # Test models endpoint
        print(f"\n🔍 Testing models endpoint...")
        try:
            response = requests.get(f"{base_url}/models", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Models endpoint: {data.get('total_available', 0)} available, {data.get('total_loaded', 0)} loaded")
            else:
                print(f"❌ Models endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Models endpoint error: {e}")
        
        # Test conversation endpoint
        print(f"\n🔍 Testing conversation endpoint...")
        try:
            response = requests.post(
                f"{base_url}/conversation",
                json={"input": "Hello, this is a test message"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Conversation endpoint: {data.get('status', 'unknown')}")
            else:
                print(f"❌ Conversation endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Conversation endpoint error: {e}")
        
        print(f"\n✅ Deployment testing completed")
        
    except Exception as e:
        print(f"❌ Error testing deployment: {e}")

def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description="DreamVault Agent Deployment")
    parser.add_argument("--config", default="configs/deployment.json", 
                       help="Deployment configuration file")
    parser.add_argument("--api-only", action="store_true", 
                       help="Start only API server")
    parser.add_argument("--web-only", action="store_true", 
                       help="Start only web interface")
    parser.add_argument("--show-config", action="store_true", 
                       help="Show deployment configuration")
    parser.add_argument("--test", action="store_true", 
                       help="Test deployment endpoints")
    
    args = parser.parse_args()
    
    setup_logging()
    
    if args.show_config:
        show_config(args.config)
        return
    
    if args.test:
        test_deployment(args.config)
        return
    
    # Start deployment
    success = start_deployment(args.config, args.api_only, args.web_only)
    
    if success:
        print("✅ Deployment completed successfully")
    else:
        print("❌ Deployment failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 