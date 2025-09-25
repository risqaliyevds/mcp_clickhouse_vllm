#!/usr/bin/env python3
"""
Mock vLLM Server for Testing
Simulates vLLM OpenAI-compatible API endpoints
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import json
import random
import time

app = FastAPI(title="Mock vLLM Server")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    stream: Optional[bool] = False
    stop: Optional[List[str]] = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    stream: Optional[bool] = False

def generate_schema_response(prompt: str) -> str:
    """Generate a mock response based on the prompt"""

    prompt_lower = prompt.lower()

    # Check for schema-related keywords
    if any(word in prompt_lower for word in ['schema', 'table', 'structure', 'column', 'database']):

        # Check for specific tool requests
        if 'get_table_schema' in prompt or 'schema for' in prompt_lower:
            # Extract table name if possible
            for table in ['users', 'orders', 'products', 'inventory', 'analytics_events']:
                if table in prompt_lower:
                    return json.dumps({
                        "use_tool": True,
                        "tool_name": "get_table_schema",
                        "arguments": {"table_name": table}
                    })

        elif 'list' in prompt_lower and 'table' in prompt_lower:
            return json.dumps({
                "use_tool": True,
                "tool_name": "list_tables",
                "arguments": {}
            })

        elif 'sample' in prompt_lower or 'data from' in prompt_lower:
            for table in ['users', 'orders', 'products', 'inventory', 'analytics_events']:
                if table in prompt_lower:
                    return json.dumps({
                        "use_tool": True,
                        "tool_name": "get_sample_data",
                        "arguments": {"table_name": table, "limit": 5}
                    })

        # If schema information is provided, generate a formatted response
        elif 'based on this' in prompt_lower or 'clickhouse schema information' in prompt_lower:
            return """Based on the provided schema information, here's a detailed analysis:

The table structure shows a well-organized database design with:

📊 **Key Observations:**
- The table uses an efficient MergeTree engine for fast queries
- Primary keys are properly configured for optimal performance
- Column types are appropriate for the data they store

💡 **Recommendations:**
1. Consider adding indexes for frequently queried columns
2. The current partitioning strategy looks optimal
3. Data types are well-chosen for storage efficiency

This schema is well-suited for analytical queries and can handle large data volumes efficiently."""

    # Default response for non-schema queries
    responses = [
        "I can help you understand your ClickHouse database schema. Try asking about specific tables!",
        "To get started, you can ask me to list available tables or show the schema for a specific table.",
        "I'm ready to help with your database queries. What would you like to know about your tables?"
    ]

    return random.choice(responses)

@app.get("/")
async def root():
    return {"message": "Mock vLLM Server Running", "version": "1.0.0"}

@app.post("/v1/completions")
async def create_completion(request: CompletionRequest):
    """OpenAI-compatible completions endpoint"""

    # Generate mock response
    generated_text = generate_schema_response(request.prompt)

    # Simulate some processing time
    time.sleep(0.1)

    return {
        "id": f"cmpl-{random.randint(1000, 9999)}",
        "object": "text_completion",
        "created": int(time.time()),
        "model": "mock-model",
        "choices": [
            {
                "text": generated_text,
                "index": 0,
                "logprobs": None,
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": len(request.prompt.split()),
            "completion_tokens": len(generated_text.split()),
            "total_tokens": len(request.prompt.split()) + len(generated_text.split())
        }
    }

@app.post("/v1/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint"""

    # Get the last user message
    last_message = ""
    for msg in reversed(request.messages):
        if msg.role == "user":
            last_message = msg.content
            break

    # Generate mock response
    generated_text = generate_schema_response(last_message)

    return {
        "id": f"chatcmpl-{random.randint(1000, 9999)}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "mock-model",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": generated_text
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": sum(len(msg.content.split()) for msg in request.messages),
            "completion_tokens": len(generated_text.split()),
            "total_tokens": sum(len(msg.content.split()) for msg in request.messages) + len(generated_text.split())
        }
    }

@app.get("/v1/models")
async def list_models():
    """List available models"""
    return {
        "object": "list",
        "data": [
            {
                "id": "mock-model",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "mock-org",
                "permission": [],
                "root": "mock-model",
                "parent": None
            }
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("🚀 Starting Mock vLLM Server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)