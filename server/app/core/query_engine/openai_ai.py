"""
OpenAI Query Engine for streaming responses with context awareness.
Integrates with short-term memory for conversation context and automatically includes
semantic memory data in the system message context for every query.
"""
import os
import json
from typing import AsyncGenerator, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.memory_manager import MemoryManager
from app.schemas.pydantic_schemas.memory_schema import Message
from app.core.query_engine.openai_tools import (
    get_episodic_memory_functions,
    execute_function_call
)
from app.db.crud.semantic_memory_crud import get_semantic_memory_by_user_id

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", ""),
    timeout=60.0,
)


async def _get_semantic_memory_context(
    db: AsyncSession,
    user_id: str
) -> str:
    """
    Retrieve and format semantic memory data for inclusion in context.
    
    Args:
        db: Database session
        user_id: User identifier
    
    Returns:
        Formatted string with semantic memory context, or empty string if not found
    """
    try:
        semantic_memory = await get_semantic_memory_by_user_id(db, user_id)
        
        if not semantic_memory or not semantic_memory.memory_data:
            return ""
        
        # Format semantic memory data as a readable context string
        memory_data = semantic_memory.memory_data
        
        # Convert dict to readable format
        context_lines = []
        context_lines.append("\n\nUser Context and Preferences:")
        
        def format_dict(data: dict, indent: int = 0) -> str:
            """Recursively format nested dictionary as readable text."""
            lines = []
            prefix = "  " * indent
            for key, value in data.items():
                if isinstance(value, dict):
                    lines.append(f"{prefix}{key}:")
                    lines.append(format_dict(value, indent + 1))
                elif isinstance(value, list):
                    lines.append(f"{prefix}{key}: {', '.join(str(v) for v in value)}")
                else:
                    lines.append(f"{prefix}{key}: {value}")
            return "\n".join(lines)
        
        formatted_data = format_dict(memory_data)
        context_lines.append(formatted_data)
        
        return "\n".join(context_lines)
        
    except Exception as e:
        # Log error but don't break the query
        print(f"[WARNING] Error retrieving semantic memory for user {user_id}: {str(e)}")
        return ""


async def stream_openai_response(
    query_text: str,
    user_id: str,
    memory_manager: MemoryManager,
    db: AsyncSession,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    enable_function_calling: bool = True,
    use_memory_queue: bool = False,
) -> AsyncGenerator[str, None]:
    """
    Stream OpenAI response for a user query with conversation context.
    Automatically includes semantic memory data in the system message context.
    
    Args:
        query_text: User's query text
        user_id: User identifier for retrieving context
        memory_manager: Memory manager instance
        db: Database session for semantic memory operations
        model: OpenAI model to use (default: gpt-4o-mini)
        temperature: Response creativity (0.0-2.0, default: 0.7)
        max_tokens: Maximum tokens in response (None = model default)
        enable_function_calling: Whether to enable function calling (currently no tools available)
        use_memory_queue: Whether to use async queue for memory operations (default: False for immediate processing)
    
    Yields:
        Response text chunks as they arrive from OpenAI
    """
    try:
        # Get recent conversation history for context
        recent_messages = await memory_manager.get_recent_messages(user_id, limit=10)
        
        # Get semantic memory context
        semantic_memory_context = await _get_semantic_memory_context(db, user_id)
        
        # Convert memory messages to OpenAI format
        messages = []
        
        # Add system message with semantic memory context
        system_content = "You are a helpful AI assistant. Provide clear, concise, and accurate responses."
        if semantic_memory_context:
            system_content += semantic_memory_context
        
        system_message = {
            "role": "system",
            "content": system_content
        }
        messages.append(system_message)
        
        # Add conversation history
        for msg in recent_messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add current user query
        messages.append({
            "role": "user",
            "content": query_text
        })
        
        # Prepare streaming parameters
        stream_params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        
        if max_tokens:
            stream_params["max_tokens"] = max_tokens
        
        # Add function calling tools if enabled and tools are available
        if enable_function_calling:
            # Combine semantic memory functions (empty) with episodic memory functions

            episodic_tools = get_episodic_memory_functions()
            tools = episodic_tools
            
            # Only add tools if there are any available
            if tools:
                stream_params["tools"] = tools
                stream_params["tool_choice"] = "auto"  # Let the model decide when to use functions
        
        # Stream response from OpenAI with function calling support
        max_iterations = 5  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            stream = await openai_client.chat.completions.create(**stream_params)
            
            function_calls = {}  # Use dict to track by index
            accumulated_content = ""
            finish_reason = None
            
            async for chunk in stream:
                # Handle function calls
                if chunk.choices[0].delta.tool_calls:
                    for tool_call_delta in chunk.choices[0].delta.tool_calls:
                        if tool_call_delta.index is not None:
                            idx = tool_call_delta.index
                            if idx not in function_calls:
                                function_calls[idx] = {
                                    "id": "",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""}
                                }
                            
                            if tool_call_delta.id:
                                function_calls[idx]["id"] = tool_call_delta.id
                            if tool_call_delta.function:
                                if tool_call_delta.function.name:
                                    function_calls[idx]["function"]["name"] = tool_call_delta.function.name
                                if tool_call_delta.function.arguments:
                                    function_calls[idx]["function"]["arguments"] += tool_call_delta.function.arguments
                
                # Handle content
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    accumulated_content += content
                    yield content
                
                # Check finish reason
                if chunk.choices[0].finish_reason:
                    finish_reason = chunk.choices[0].finish_reason
            
            # Check if we need to execute function calls
            if finish_reason == "tool_calls" and function_calls:
                # First, add the assistant message with tool_calls to messages
                # This is required by OpenAI - tool responses must follow an assistant message with tool_calls
                assistant_message = {
                    "role": "assistant",
                    "content": accumulated_content if accumulated_content else None,
                    "tool_calls": [
                        {
                            "id": tool_call["id"],
                            "type": "function",
                            "function": {
                                "name": tool_call["function"]["name"],
                                "arguments": tool_call["function"]["arguments"]
                            }
                        }
                        for tool_call in function_calls.values()
                        if tool_call["function"]["name"]
                    ]
                }
                messages.append(assistant_message)
                
                # Execute all function calls
                for idx, tool_call in function_calls.items():
                    if tool_call["function"]["name"]:
                        function_name = tool_call["function"]["name"]
                        arguments_str = tool_call["function"]["arguments"]
                        
                        # Debug logging
                        print(f"[DEBUG] Function call: {function_name}")
                        print(f"[DEBUG] Arguments string: {arguments_str}")
                        
                        try:
                            function_args = json.loads(arguments_str)
                            print(f"[DEBUG] Parsed arguments: {function_args}")
                        except json.JSONDecodeError as e:
                            print(f"[ERROR] Failed to parse JSON arguments: {e}")
                            print(f"[ERROR] Raw arguments string: {repr(arguments_str)}")
                            # Try to handle incomplete JSON (might happen during streaming)
                            # If arguments string is empty or incomplete, skip this function call
                            if not arguments_str or arguments_str.strip() == "":
                                print(f"[WARNING] Empty arguments string for {function_name}, skipping")
                                continue
                            function_args = {}
                        
                        # Execute function
                        function_result = await execute_function_call(
                            db, user_id, function_name, function_args, use_queue=use_memory_queue
                        )
                        print(f"[DEBUG] Function result: {function_result}")
                        
                        # Add function result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": function_name,
                            "content": json.dumps(function_result)
                        })
                
                # Continue conversation with function results
                # Update stream_params for next iteration
                if iteration < max_iterations:
                    continue
                else:
                    break
            else:
                # No function calls or finished normally, we're done
                break
        
    except Exception as e:
        error_message = f"Error generating response: {str(e)}"
        print(error_message)
        yield f"\n\n[Error: {error_message}]"
        raise


async def get_openai_response(
    query_text: str,
    user_id: str,
    memory_manager: MemoryManager,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Get a complete OpenAI response (non-streaming) for a user query.
    
    Args:
        query_text: User's query text
        user_id: User identifier for retrieving context
        memory_manager: Memory manager instance
        model: OpenAI model to use
        temperature: Response creativity
        max_tokens: Maximum tokens in response
    
    Returns:
        Complete response text
    """
    try:
        # Get recent conversation history
        recent_messages = await memory_manager.get_recent_messages(user_id, limit=20)
        
        # Convert to OpenAI format
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant. Provide clear, concise, and accurate responses."
            }
        ]
        
        for msg in recent_messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        messages.append({
            "role": "user",
            "content": query_text
        })
        
        # Get response from OpenAI
        response_params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            response_params["max_tokens"] = max_tokens
        
        response = await openai_client.chat.completions.create(**response_params)
        
        return response.choices[0].message.content
        
    except Exception as e:
        error_message = f"Error generating response: {str(e)}"
        print(error_message)
        raise Exception(error_message)