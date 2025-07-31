# 🚀 DreamVault Agent Deployment System

Deploy your trained AI agents with a complete API server and web interface.

## 🎯 Overview

The DreamVault Deployment System provides:

- **🔧 REST API Server** - Serve trained agents via HTTP endpoints
- **🌐 Web Interface** - Modern, responsive web UI for agent interaction
- **🤖 Model Manager** - Intelligent model loading, caching, and health monitoring
- **⚙️ Configuration Management** - Flexible deployment configuration

## 🚀 Quick Start

### 1. Train Your Agents
```bash
# Train agents first (if not already done)
python run_agent_training.py --api-key YOUR_OPENAI_API_KEY
```

### 2. Deploy Agents
```bash
# Start full deployment (API + Web Interface)
python run_deployment.py

# Start API server only
python run_deployment.py --api-only

# Start web interface only
python run_deployment.py --web-only
```

### 3. Access Your Agents
- **Web Interface**: http://localhost:8080
- **API Server**: http://localhost:8000
- **Health Check**: http://localhost:8000/health

## 📋 Configuration

### View Configuration
```bash
python run_deployment.py --show-config
```

### Default Configuration
```json
{
  "api_server": {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": false,
    "cors_enabled": true,
    "rate_limit": {
      "enabled": true,
      "requests_per_minute": 60
    }
  },
  "web_interface": {
    "host": "0.0.0.0",
    "port": 8080,
    "auto_open_browser": true,
    "theme": "default"
  },
  "model_manager": {
    "models_dir": "models",
    "auto_load_models": true,
    "health_check_interval": 300,
    "max_models_in_memory": 5
  },
  "security": {
    "api_key_required": false,
    "allowed_origins": ["*"],
    "max_request_size": "10MB"
  },
  "performance": {
    "enable_caching": true,
    "cache_ttl": 3600,
    "max_concurrent_requests": 10
  }
}
```

## 🔧 API Endpoints

### Health & Status
```bash
# Health check
GET /health

# List models
GET /models

# Model statistics
GET /models/{model_name}/stats
```

### Model Management
```bash
# Load model
POST /models/{model_name}/load
{
  "force_reload": false
}

# Unload model
POST /models/{model_name}/unload
```

### Agent Endpoints

#### Conversation Agent
```bash
POST /conversation
{
  "input": "Hello, how are you?",
  "model": "conversation_agent"  # optional
}
```

#### Summarization Agent
```bash
POST /summarize
{
  "text": "Long text to summarize...",
  "model": "summarization_agent"  # optional
}
```

#### Q&A Agent
```bash
POST /qa
{
  "question": "What was discussed?",
  "context": "Context information...",
  "model": "qa_agent"  # optional
}
```

#### Instruction Agent
```bash
POST /instruction
{
  "instruction": "Please help me with this task",
  "model": "instruction_agent"  # optional
}
```

#### Embedding Agent
```bash
POST /embed
{
  "text": "Text to embed",
  "model": "embedding_agent"  # optional
}
```

#### Generic Agent
```bash
POST /agent/{agent_type}
{
  "input": "Your input here",
  "model": "model_name"  # optional
}
```

## 🌐 Web Interface

The web interface provides a modern, responsive UI for interacting with your agents:

### Features
- **💬 Chat Interface** - Talk with conversation agents
- **📝 Text Summarization** - Summarize long texts
- **❓ Q&A Interface** - Ask questions with context
- **📋 Instruction Following** - Give instructions to agents
- **📊 Real-time Status** - Monitor system health
- **📱 Mobile Responsive** - Works on all devices

### Usage
1. Open http://localhost:8080 in your browser
2. Choose the agent type you want to use
3. Enter your input and click the action button
4. View the response in real-time

## 🤖 Model Manager

The Model Manager handles intelligent model loading and management:

### Features
- **🔍 Auto-discovery** - Automatically finds trained models
- **💾 Smart Caching** - Keeps frequently used models in memory
- **🏥 Health Monitoring** - Continuous health checks
- **📊 Performance Tracking** - Request statistics and response times
- **🔄 Dynamic Loading** - Load/unload models on demand

### Model Types Supported
- **OpenAI Fine-tuned** - GPT-3.5-turbo fine-tuned models
- **Hugging Face** - Local transformer models
- **Sentence Transformers** - Embedding models

## 🔒 Security Features

### API Security
- **CORS Support** - Configurable cross-origin requests
- **Rate Limiting** - Prevent abuse with request limits
- **Request Size Limits** - Protect against large payloads
- **API Key Authentication** - Optional API key requirement

### Web Security
- **HTTPS Ready** - Configure SSL certificates
- **Input Validation** - Sanitize user inputs
- **XSS Protection** - Prevent cross-site scripting

## ⚡ Performance Optimization

### Caching
- **Response Caching** - Cache frequent responses
- **Model Caching** - Keep models in memory
- **Configurable TTL** - Set cache expiration times

### Concurrency
- **Request Queuing** - Handle multiple concurrent requests
- **Model Pooling** - Efficient model resource management
- **Background Processing** - Non-blocking operations

## 🧪 Testing

### Test Deployment
```bash
# Test all endpoints
python run_deployment.py --test

# Test deployment system
python test_deployment_system.py
```

### Manual Testing
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test conversation agent
curl -X POST http://localhost:8000/conversation \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello, how are you?"}'

# Test summarization
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "Long text to summarize..."}'
```

## 📊 Monitoring

### Health Checks
```bash
# Check API health
curl http://localhost:8000/health

# Check model status
curl http://localhost:8000/models
```

### Logs
- **API Logs**: `deployment.log`
- **Model Logs**: Console output
- **Error Logs**: Detailed error tracking

### Metrics
- **Request Count** - Total requests per model
- **Response Time** - Average response times
- **Error Rate** - Error statistics
- **Memory Usage** - Model memory consumption

## 🔧 Advanced Configuration

### Custom Ports
```bash
# Edit configs/deployment.json
{
  "api_server": {
    "port": 9000
  },
  "web_interface": {
    "port": 9090
  }
}
```

### Production Settings
```json
{
  "api_server": {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": false,
    "rate_limit": {
      "enabled": true,
      "requests_per_minute": 30
    }
  },
  "security": {
    "api_key_required": true,
    "allowed_origins": ["https://yourdomain.com"]
  },
  "performance": {
    "enable_caching": true,
    "max_concurrent_requests": 20
  }
}
```

### SSL/HTTPS
```bash
# Configure SSL certificates
python run_deployment.py --config production_config.json
```

## 🚀 Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000 8080

CMD ["python", "run_deployment.py"]
```

### Systemd Service
```ini
[Unit]
Description=DreamVault Agent Deployment
After=network.target

[Service]
Type=simple
User=dreamvault
WorkingDirectory=/opt/dreamvault
ExecStart=/usr/bin/python3 run_deployment.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔍 Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Check what's using the port
netstat -tulpn | grep :8000

# Change port in configuration
python run_deployment.py --config custom_config.json
```

**Model Loading Failed**
```bash
# Check model directory
ls -la models/

# Test model loading
python test_deployment_system.py
```

**API Not Responding**
```bash
# Check if server is running
curl http://localhost:8000/health

# Check logs
tail -f deployment.log
```

**Web Interface Not Loading**
```bash
# Check if web server is running
curl http://localhost:8080

# Check browser console for errors
```

### Performance Issues

**Slow Response Times**
- Increase `max_concurrent_requests`
- Enable caching
- Use GPU for model inference

**High Memory Usage**
- Reduce `max_models_in_memory`
- Unload unused models
- Use smaller model variants

**API Rate Limiting**
- Increase `requests_per_minute`
- Implement client-side caching
- Use batch requests

## 📚 API Examples

### Python Client
```python
import requests

# Conversation agent
response = requests.post('http://localhost:8000/conversation', 
    json={'input': 'Hello, how are you?'})
print(response.json()['response'])

# Summarization agent
response = requests.post('http://localhost:8000/summarize',
    json={'text': 'Long text to summarize...'})
print(response.json()['response'])
```

### JavaScript Client
```javascript
// Conversation agent
const response = await fetch('http://localhost:8000/conversation', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({input: 'Hello, how are you?'})
});
const data = await response.json();
console.log(data.response);
```

### cURL Examples
```bash
# Load a model
curl -X POST http://localhost:8000/models/conversation_agent/load

# Get model stats
curl http://localhost:8000/models/conversation_agent/stats

# Test conversation
curl -X POST http://localhost:8000/conversation \
  -H "Content-Type: application/json" \
  -d '{"input": "Tell me a joke"}'
```

## 🎯 Next Steps

After deploying your agents:

1. **Monitor Performance** - Track response times and usage
2. **Scale Up** - Add more models and endpoints
3. **Customize UI** - Modify web interface for your needs
4. **Add Authentication** - Implement user authentication
5. **Deploy to Cloud** - Move to production cloud environment

---

**Ready to deploy your AI agents?** 🚀

```bash
# Start deployment
python run_deployment.py

# Access your agents
# Web UI: http://localhost:8080
# API: http://localhost:8000
``` 