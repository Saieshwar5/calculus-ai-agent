from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import Optional, List
from app.schemas.pydantic_schemas.chat_schema import ChatRequest, ChatResponse


chat_router = APIRouter()


@chat_router.post("/send-message", response_model=ChatResponse ,  status_code=200)
async def chat(request: ChatRequest) -> ChatResponse:

    print(request.message)

    if not request.message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    else:
        return ChatResponse(message=request.message)


