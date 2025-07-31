"""
Web Interface for DreamVault Agent Deployment

Provides a modern web UI for interacting with trained AI agents.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import webbrowser
import threading
import time

try:
    from flask import Flask, render_template, request, jsonify, send_from_directory
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None

logger = logging.getLogger(__name__)

class AgentWebInterface:
    """
    Web interface for DreamVault AI agents.
    
    Provides a modern, responsive web UI for:
    - Chatting with conversation agents
    - Summarizing text
    - Asking questions
    - Following instructions
    - Generating embeddings
    - Model management
    """
    
    def __init__(self, api_url: str = "http://localhost:8000", host: str = "0.0.0.0", port: int = 8080):
        """
        Initialize the web interface.
        
        Args:
            api_url: URL of the API server
            host: Web server host address
            port: Web server port
        """
        if not FLASK_AVAILABLE:
            raise ImportError("Flask is required for web interface. Install with: pip install flask flask-cors")
        
        self.api_url = api_url.rstrip('/')
        self.host = host
        self.port = port
        
        # Initialize Flask app
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Register routes
        self._register_routes()
        
        # Server thread
        self.server_thread = None
        self.running = False
        
        logger.info(f"✅ Web Interface initialized: http://{host}:{port}")
    
    def _register_routes(self):
        """Register web routes."""
        
        @self.app.route('/')
        def index():
            """Main interface page."""
            return self._render_main_interface()
        
        @self.app.route('/api/proxy/<path:endpoint>', methods=['GET', 'POST'])
        def api_proxy(endpoint):
            """Proxy API requests to the backend."""
            return self._proxy_api_request(endpoint, request)
        
        @self.app.route('/static/<path:filename>')
        def static_files(filename):
            """Serve static files."""
            return self._serve_static_file(filename)
    
    def _render_main_interface(self) -> str:
        """Render the main web interface."""
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DreamVault AI Agents</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            color: white;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5rem;
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        .input-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }
        
        .input-group input,
        .input-group textarea,
        .input-group select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s ease;
        }
        
        .input-group input:focus,
        .input-group textarea:focus,
        .input-group select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .input-group textarea {
            resize: vertical;
            min-height: 100px;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: transform 0.2s ease;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .response-area {
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            min-height: 100px;
            white-space: pre-wrap;
        }
        
        .chat-container {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #e1e5e9;
            border-radius: 8px;
            padding: 15px;
            background: #f8f9fa;
        }
        
        .chat-message {
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 10px;
            max-width: 80%;
        }
        
        .chat-message.user {
            background: #667eea;
            color: white;
            margin-left: auto;
        }
        
        .chat-message.assistant {
            background: white;
            border: 1px solid #e1e5e9;
        }
        
        .status-bar {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-top: 30px;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }
        
        .status-item {
            text-align: center;
        }
        
        .status-item h3 {
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .loading {
            display: none;
            text-align: center;
            margin: 20px 0;
        }
        
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 DreamVault AI Agents</h1>
            <p>Your personalized AI assistants, trained on your conversation data</p>
        </div>
        
        <div class="main-content">
            <!-- Conversation Agent -->
            <div class="card">
                <h2>💬 Conversation Agent</h2>
                <div class="input-group">
                    <label for="conversation-input">Message:</label>
                    <textarea id="conversation-input" placeholder="Type your message here..."></textarea>
                </div>
                <button class="btn" onclick="sendConversation()">Send Message</button>
                <div class="loading" id="conversation-loading">
                    <div class="spinner"></div>
                    <p>Generating response...</p>
                </div>
                <div class="response-area" id="conversation-response"></div>
            </div>
            
            <!-- Summarization Agent -->
            <div class="card">
                <h2>📝 Summarization Agent</h2>
                <div class="input-group">
                    <label for="summarize-text">Text to Summarize:</label>
                    <textarea id="summarize-text" placeholder="Paste text to summarize..."></textarea>
                </div>
                <button class="btn" onclick="summarizeText()">Summarize</button>
                <div class="loading" id="summarize-loading">
                    <div class="spinner"></div>
                    <p>Generating summary...</p>
                </div>
                <div class="response-area" id="summarize-response"></div>
            </div>
            
            <!-- Q&A Agent -->
            <div class="card">
                <h2>❓ Q&A Agent</h2>
                <div class="input-group">
                    <label for="qa-question">Question:</label>
                    <input type="text" id="qa-question" placeholder="Ask a question...">
                </div>
                <div class="input-group">
                    <label for="qa-context">Context (optional):</label>
                    <textarea id="qa-context" placeholder="Provide context for the question..."></textarea>
                </div>
                <button class="btn" onclick="askQuestion()">Ask Question</button>
                <div class="loading" id="qa-loading">
                    <div class="spinner"></div>
                    <p>Finding answer...</p>
                </div>
                <div class="response-area" id="qa-response"></div>
            </div>
            
            <!-- Instruction Agent -->
            <div class="card">
                <h2>📋 Instruction Agent</h2>
                <div class="input-group">
                    <label for="instruction-text">Instruction:</label>
                    <textarea id="instruction-text" placeholder="Give an instruction..."></textarea>
                </div>
                <button class="btn" onclick="followInstruction()">Follow Instruction</button>
                <div class="loading" id="instruction-loading">
                    <div class="spinner"></div>
                    <p>Processing instruction...</p>
                </div>
                <div class="response-area" id="instruction-response"></div>
            </div>
        </div>
        
        <!-- Status Bar -->
        <div class="status-bar">
            <h2>📊 System Status</h2>
            <div class="status-grid">
                <div class="status-item">
                    <h3 id="models-loaded">0</h3>
                    <p>Models Loaded</p>
                </div>
                <div class="status-item">
                    <h3 id="api-status">Checking...</h3>
                    <p>API Status</p>
                </div>
                <div class="status-item">
                    <h3 id="total-requests">0</h3>
                    <p>Total Requests</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let totalRequests = 0;
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            checkAPIStatus();
            loadModels();
        });
        
        async function checkAPIStatus() {
            try {
                const response = await fetch('/api/proxy/health');
                const data = await response.json();
                document.getElementById('api-status').textContent = 'Online';
                document.getElementById('api-status').style.color = '#28a745';
            } catch (error) {
                document.getElementById('api-status').textContent = 'Offline';
                document.getElementById('api-status').style.color = '#dc3545';
            }
        }
        
        async function loadModels() {
            try {
                const response = await fetch('/api/proxy/models');
                const data = await response.json();
                document.getElementById('models-loaded').textContent = data.total_loaded || 0;
            } catch (error) {
                console.error('Error loading models:', error);
            }
        }
        
        async function sendConversation() {
            const input = document.getElementById('conversation-input').value.trim();
            if (!input) return;
            
            showLoading('conversation');
            totalRequests++;
            document.getElementById('total-requests').textContent = totalRequests;
            
            try {
                const response = await fetch('/api/proxy/conversation', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({input: input})
                });
                
                const data = await response.json();
                hideLoading('conversation');
                
                if (data.status === 'success') {
                    document.getElementById('conversation-response').textContent = data.response;
                } else {
                    document.getElementById('conversation-response').textContent = 'Error: ' + data.error;
                }
            } catch (error) {
                hideLoading('conversation');
                document.getElementById('conversation-response').textContent = 'Error: ' + error.message;
            }
        }
        
        async function summarizeText() {
            const text = document.getElementById('summarize-text').value.trim();
            if (!text) return;
            
            showLoading('summarize');
            totalRequests++;
            document.getElementById('total-requests').textContent = totalRequests;
            
            try {
                const response = await fetch('/api/proxy/summarize', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text: text})
                });
                
                const data = await response.json();
                hideLoading('summarize');
                
                if (data.status === 'success') {
                    document.getElementById('summarize-response').textContent = data.response;
                } else {
                    document.getElementById('summarize-response').textContent = 'Error: ' + data.error;
                }
            } catch (error) {
                hideLoading('summarize');
                document.getElementById('summarize-response').textContent = 'Error: ' + error.message;
            }
        }
        
        async function askQuestion() {
            const question = document.getElementById('qa-question').value.trim();
            const context = document.getElementById('qa-context').value.trim();
            if (!question) return;
            
            showLoading('qa');
            totalRequests++;
            document.getElementById('total-requests').textContent = totalRequests;
            
            try {
                const response = await fetch('/api/proxy/qa', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        question: question,
                        context: context
                    })
                });
                
                const data = await response.json();
                hideLoading('qa');
                
                if (data.status === 'success') {
                    document.getElementById('qa-response').textContent = data.response;
                } else {
                    document.getElementById('qa-response').textContent = 'Error: ' + data.error;
                }
            } catch (error) {
                hideLoading('qa');
                document.getElementById('qa-response').textContent = 'Error: ' + error.message;
            }
        }
        
        async function followInstruction() {
            const instruction = document.getElementById('instruction-text').value.trim();
            if (!instruction) return;
            
            showLoading('instruction');
            totalRequests++;
            document.getElementById('total-requests').textContent = totalRequests;
            
            try {
                const response = await fetch('/api/proxy/instruction', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({instruction: instruction})
                });
                
                const data = await response.json();
                hideLoading('instruction');
                
                if (data.status === 'success') {
                    document.getElementById('instruction-response').textContent = data.response;
                } else {
                    document.getElementById('instruction-response').textContent = 'Error: ' + data.error;
                }
            } catch (error) {
                hideLoading('instruction');
                document.getElementById('instruction-response').textContent = 'Error: ' + error.message;
            }
        }
        
        function showLoading(type) {
            document.getElementById(type + '-loading').style.display = 'block';
            document.getElementById(type + '-response').textContent = '';
        }
        
        function hideLoading(type) {
            document.getElementById(type + '-loading').style.display = 'none';
        }
        
        // Auto-refresh status every 30 seconds
        setInterval(() => {
            checkAPIStatus();
            loadModels();
        }, 30000);
    </script>
</body>
</html>
        """
        return html
    
    def _proxy_api_request(self, endpoint: str, request):
        """Proxy API requests to the backend."""
        try:
            import requests
            
            url = f"{self.api_url}/{endpoint}"
            
            if request.method == 'GET':
                response = requests.get(url)
            elif request.method == 'POST':
                response = requests.post(url, json=request.json)
            else:
                return jsonify({"error": "Method not allowed"}), 405
            
            return response.json(), response.status_code
            
        except Exception as e:
            logger.error(f"API proxy error: {e}")
            return jsonify({"error": str(e)}), 500
    
    def _serve_static_file(self, filename: str):
        """Serve static files."""
        # For now, return 404 since we're embedding everything in HTML
        return "File not found", 404
    
    def start(self, open_browser: bool = True):
        """
        Start the web interface.
        
        Args:
            open_browser: Automatically open browser
        """
        if self.running:
            logger.warning("Web interface already running")
            return
        
        # Start server in thread
        self.running = True
        self.server_thread = threading.Thread(
            target=self._run_server,
            daemon=True
        )
        self.server_thread.start()
        
        # Wait a moment for server to start
        time.sleep(2)
        
        # Open browser
        if open_browser:
            url = f"http://{self.host}:{self.port}"
            webbrowser.open(url)
        
        logger.info(f"✅ Web Interface started: http://{self.host}:{self.port}")
    
    def _run_server(self):
        """Run the Flask server."""
        try:
            self.app.run(
                host=self.host,
                port=self.port,
                debug=False,
                use_reloader=False
            )
        except Exception as e:
            logger.error(f"Web interface error: {e}")
            self.running = False
    
    def stop(self):
        """Stop the web interface."""
        self.running = False
        logger.info("✅ Web Interface stopped")
    
    def is_running(self) -> bool:
        """Check if web interface is running."""
        return self.running 