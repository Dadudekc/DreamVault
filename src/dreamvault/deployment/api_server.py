"""
API Server for DreamVault Agent Deployment

Provides REST API endpoints for trained AI agents.
"""

import json
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
import threading

try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None
    jsonify = None

from .model_manager import ModelManager

logger = logging.getLogger(__name__)

class AgentAPIServer:
    """
    REST API server for DreamVault AI agents.
    
    Provides endpoints for:
    - Model management (load/unload/list)
    - Agent inference (conversation, summarization, Q&A, etc.)
    - Health checks and monitoring
    """
    
    def __init__(self, models_dir: str = "models", host: str = "0.0.0.0", port: int = 8000):
        """
        Initialize the API server.
        
        Args:
            models_dir: Directory containing trained models
            host: Server host address
            port: Server port
        """
        if not FLASK_AVAILABLE:
            raise ImportError("Flask is required for API server. Install with: pip install flask flask-cors")
        
        self.host = host
        self.port = port
        self.model_manager = ModelManager(models_dir)
        
        # Initialize Flask app
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for all routes
        
        # Register routes
        self._register_routes()
        
        # Server thread
        self.server_thread = None
        self.running = False
        
        logger.info(f"✅ API Server initialized: {host}:{port}")
    
    def _register_routes(self):
        """Register API routes."""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "models_loaded": len(self.model_manager.loaded_models)
            })
        
        @self.app.route('/models', methods=['GET'])
        def list_models():
            """List all available and loaded models."""
            try:
                models_info = self.model_manager.list_models()
                return jsonify(models_info)
            except Exception as e:
                logger.error(f"Error listing models: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/models/<model_name>/load', methods=['POST'])
        def load_model(model_name):
            """Load a model."""
            try:
                force_reload = request.json.get('force_reload', False) if request.json else False
                success = self.model_manager.load_model(model_name, force_reload)
                
                if success:
                    return jsonify({
                        "status": "success",
                        "message": f"Model {model_name} loaded successfully"
                    })
                else:
                    return jsonify({
                        "status": "error",
                        "message": f"Failed to load model {model_name}"
                    }), 400
            except Exception as e:
                logger.error(f"Error loading model {model_name}: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/models/<model_name>/unload', methods=['POST'])
        def unload_model(model_name):
            """Unload a model."""
            try:
                success = self.model_manager.unload_model(model_name)
                
                if success:
                    return jsonify({
                        "status": "success",
                        "message": f"Model {model_name} unloaded successfully"
                    })
                else:
                    return jsonify({
                        "status": "error",
                        "message": f"Failed to unload model {model_name}"
                    }), 400
            except Exception as e:
                logger.error(f"Error unloading model {model_name}: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/models/<model_name>/stats', methods=['GET'])
        def get_model_stats(model_name):
            """Get model statistics."""
            try:
                stats = self.model_manager.get_model_stats(model_name)
                if stats:
                    return jsonify(stats)
                else:
                    return jsonify({"error": f"Model {model_name} not found"}), 404
            except Exception as e:
                logger.error(f"Error getting stats for {model_name}: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/conversation', methods=['POST'])
        def conversation():
            """Conversation agent endpoint."""
            return self._handle_agent_request('conversation_agent', request)
        
        @self.app.route('/summarize', methods=['POST'])
        def summarize():
            """Summarization agent endpoint."""
            return self._handle_agent_request('summarization_agent', request)
        
        @self.app.route('/qa', methods=['POST'])
        def qa():
            """Q&A agent endpoint."""
            return self._handle_agent_request('qa_agent', request)
        
        @self.app.route('/instruction', methods=['POST'])
        def instruction():
            """Instruction agent endpoint."""
            return self._handle_agent_request('instruction_agent', request)
        
        @self.app.route('/embed', methods=['POST'])
        def embed():
            """Embedding agent endpoint."""
            return self._handle_agent_request('embedding_agent', request)
        
        @self.app.route('/agent/<agent_type>', methods=['POST'])
        def generic_agent(agent_type):
            """Generic agent endpoint."""
            return self._handle_agent_request(agent_type, request)
    
    def _handle_agent_request(self, agent_type: str, request):
        """Handle agent inference requests."""
        start_time = time.time()
        
        try:
            # Parse request
            if not request.json:
                return jsonify({"error": "No JSON data provided"}), 400
            
            data = request.json
            model_name = data.get('model', agent_type)
            
            # Load model if not already loaded
            if not self.model_manager.get_model(model_name):
                success = self.model_manager.load_model(model_name)
                if not success:
                    return jsonify({
                        "error": f"Failed to load model {model_name}"
                    }), 400
            
            # Get model
            model_data = self.model_manager.get_model(model_name)
            if not model_data:
                return jsonify({
                    "error": f"Model {model_name} not available"
                }), 400
            
            # Process request based on agent type
            if agent_type == 'conversation_agent':
                response = self._process_conversation(model_data, data)
            elif agent_type == 'summarization_agent':
                response = self._process_summarization(model_data, data)
            elif agent_type == 'qa_agent':
                response = self._process_qa(model_data, data)
            elif agent_type == 'instruction_agent':
                response = self._process_instruction(model_data, data)
            elif agent_type == 'embedding_agent':
                response = self._process_embedding(model_data, data)
            else:
                return jsonify({
                    "error": f"Unknown agent type: {agent_type}"
                }), 400
            
            # Update statistics
            response_time = time.time() - start_time
            self.model_manager.update_model_stats(model_name, response_time, True)
            
            return jsonify({
                "status": "success",
                "response": response,
                "model": model_name,
                "response_time": response_time
            })
            
        except Exception as e:
            response_time = time.time() - start_time
            if 'model_name' in locals():
                self.model_manager.update_model_stats(model_name, response_time, False)
            
            logger.error(f"Error processing {agent_type} request: {e}")
            return jsonify({
                "error": str(e),
                "response_time": response_time
            }), 500
    
    def _process_conversation(self, model_data: Dict[str, Any], request_data: Dict[str, Any]) -> str:
        """Process conversation request."""
        input_text = request_data.get('input', '')
        if not input_text:
            raise ValueError("Input text is required")
        
        model_type = model_data['type']
        
        if model_type == 'openai':
            # Use OpenAI API
            return self._call_openai_conversation(model_data, input_text)
        elif model_type == 'huggingface':
            # Use local Hugging Face model
            return self._call_huggingface_conversation(model_data, input_text)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
    
    def _process_summarization(self, model_data: Dict[str, Any], request_data: Dict[str, Any]) -> str:
        """Process summarization request."""
        text = request_data.get('text', '')
        if not text:
            raise ValueError("Text to summarize is required")
        
        model_type = model_data['type']
        
        if model_type == 'openai':
            return self._call_openai_summarization(model_data, text)
        elif model_type == 'huggingface':
            return self._call_huggingface_summarization(model_data, text)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
    
    def _process_qa(self, model_data: Dict[str, Any], request_data: Dict[str, Any]) -> str:
        """Process Q&A request."""
        question = request_data.get('question', '')
        context = request_data.get('context', '')
        
        if not question:
            raise ValueError("Question is required")
        
        model_type = model_data['type']
        
        if model_type == 'openai':
            return self._call_openai_qa(model_data, question, context)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
    
    def _process_instruction(self, model_data: Dict[str, Any], request_data: Dict[str, Any]) -> str:
        """Process instruction request."""
        instruction = request_data.get('instruction', '')
        if not instruction:
            raise ValueError("Instruction is required")
        
        model_type = model_data['type']
        
        if model_type == 'openai':
            return self._call_openai_instruction(model_data, instruction)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
    
    def _process_embedding(self, model_data: Dict[str, Any], request_data: Dict[str, Any]) -> list:
        """Process embedding request."""
        text = request_data.get('text', '')
        if not text:
            raise ValueError("Text for embedding is required")
        
        model_type = model_data['type']
        
        if model_type == 'sentence_transformers':
            return self._call_sentence_transformers_embedding(model_data, text)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
    
    def _call_openai_conversation(self, model_data: Dict[str, Any], input_text: str) -> str:
        """Call OpenAI conversation model."""
        try:
            import openai
            
            # Get model ID from job info
            job_info = model_data.get('job_info', {})
            model_id = job_info.get('model_id', 'gpt-3.5-turbo')
            
            response = openai.ChatCompletion.create(
                model=model_id,
                messages=[
                    {"role": "user", "content": input_text}
                ],
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI conversation error: {e}")
            return f"Error: {str(e)}"
    
    def _call_huggingface_conversation(self, model_data: Dict[str, Any], input_text: str) -> str:
        """Call Hugging Face conversation model."""
        try:
            model = model_data['model']
            tokenizer = model_data['tokenizer']
            
            # Format input
            formatted_input = f"User: {input_text}\nAssistant:"
            
            # Tokenize
            inputs = tokenizer.encode(formatted_input, return_tensors="pt", max_length=512, truncation=True)
            
            # Generate
            outputs = model.generate(
                inputs,
                max_length=512,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
            
            # Decode
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract assistant response
            if "Assistant:" in response:
                response = response.split("Assistant:")[-1].strip()
            
            return response
            
        except Exception as e:
            logger.error(f"Hugging Face conversation error: {e}")
            return f"Error: {str(e)}"
    
    def _call_openai_summarization(self, model_data: Dict[str, Any], text: str) -> str:
        """Call OpenAI summarization model."""
        try:
            import openai
            
            job_info = model_data.get('job_info', {})
            model_id = job_info.get('model_id', 'gpt-3.5-turbo')
            
            response = openai.ChatCompletion.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": "Summarize the following text:"},
                    {"role": "user", "content": text}
                ],
                max_tokens=200
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI summarization error: {e}")
            return f"Error: {str(e)}"
    
    def _call_huggingface_summarization(self, model_data: Dict[str, Any], text: str) -> str:
        """Call Hugging Face summarization model."""
        try:
            model = model_data['model']
            tokenizer = model_data['tokenizer']
            
            # Tokenize
            inputs = tokenizer.encode(text, return_tensors="pt", max_length=512, truncation=True)
            
            # Generate summary
            outputs = model.generate(
                inputs,
                max_length=128,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
            
            # Decode
            summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            return summary
            
        except Exception as e:
            logger.error(f"Hugging Face summarization error: {e}")
            return f"Error: {str(e)}"
    
    def _call_openai_qa(self, model_data: Dict[str, Any], question: str, context: str) -> str:
        """Call OpenAI Q&A model."""
        try:
            import openai
            
            job_info = model_data.get('job_info', {})
            model_id = job_info.get('model_id', 'gpt-3.5-turbo')
            
            prompt = f"Context: {context}\n\nQuestion: {question}\n\nAnswer:"
            
            response = openai.ChatCompletion.create(
                model=model_id,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI Q&A error: {e}")
            return f"Error: {str(e)}"
    
    def _call_openai_instruction(self, model_data: Dict[str, Any], instruction: str) -> str:
        """Call OpenAI instruction model."""
        try:
            import openai
            
            job_info = model_data.get('job_info', {})
            model_id = job_info.get('model_id', 'gpt-3.5-turbo')
            
            response = openai.ChatCompletion.create(
                model=model_id,
                messages=[
                    {"role": "user", "content": instruction}
                ],
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI instruction error: {e}")
            return f"Error: {str(e)}"
    
    def _call_sentence_transformers_embedding(self, model_data: Dict[str, Any], text: str) -> list:
        """Call sentence transformers embedding model."""
        try:
            model = model_data['model']
            embedding = model.encode(text)
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Sentence transformers embedding error: {e}")
            return []
    
    def start(self, debug: bool = False):
        """
        Start the API server.
        
        Args:
            debug: Run in debug mode
        """
        if self.running:
            logger.warning("API server already running")
            return
        
        # Start model manager health checks
        self.model_manager.start_health_check()
        
        # Start server in thread
        self.running = True
        self.server_thread = threading.Thread(
            target=self._run_server,
            args=(debug,),
            daemon=True
        )
        self.server_thread.start()
        
        logger.info(f"✅ API Server started: http://{self.host}:{self.port}")
    
    def _run_server(self, debug: bool):
        """Run the Flask server."""
        try:
            self.app.run(
                host=self.host,
                port=self.port,
                debug=debug,
                use_reloader=False
            )
        except Exception as e:
            logger.error(f"API server error: {e}")
            self.running = False
    
    def stop(self):
        """Stop the API server."""
        self.running = False
        
        # Stop model manager
        self.model_manager.cleanup()
        
        logger.info("✅ API Server stopped")
    
    def is_running(self) -> bool:
        """Check if server is running."""
        return self.running 