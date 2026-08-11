import json
from typing import Optional, AsyncGenerator
from sqlalchemy.orm import Session
from app.models.conversation import Conversation, ChatMessage


async def stream_and_save(
    stream_generator: AsyncGenerator,
    db: Session,
    user_id: int,
    conversation_id: Optional[int],
    user_message: str,
    api_id: Optional[int],
    conversation_mode: str = "chat"
) -> AsyncGenerator:
    full_content = ""
    
    async for chunk in stream_generator:
        if chunk.startswith("data: "):
            data = chunk[6:]
            if data == "[DONE]":
                break
            try:
                parsed = json.loads(data)
                if "content" in parsed:
                    full_content += parsed["content"]
            except (json.JSONDecodeError, TypeError):
                pass
        yield chunk
    
    if not conversation_id:
        new_conversation = Conversation(
            user_id=user_id,
            title=user_message[:50] if len(user_message) > 50 else user_message,
            conversation_mode=conversation_mode,
            api_id=api_id
        )
        db.add(new_conversation)
        db.flush()
        conversation_id = new_conversation.id
    
    user_msg = ChatMessage(
        conversation_id=conversation_id,
        role="user",
        content=user_message
    )
    db.add(user_msg)
    db.flush()
    
    assistant_msg = ChatMessage(
        conversation_id=conversation_id,
        role="assistant",
        content=full_content
    )
    db.add(assistant_msg)
    db.flush()
    
    db.commit()
    
    yield f"data: {json.dumps({'type': 'saved', 'conversation_id': conversation_id, 'message_id': assistant_msg.id})}\n\n"
    yield "data: [DONE]\n\n"


def save_conversation_messages(
    db: Session,
    user_id: int,
    conversation_id: Optional[int],
    user_message: str,
    assistant_message: str,
    api_id: Optional[int],
    conversation_mode: str = "chat"
) -> tuple:
    if not conversation_id:
        new_conversation = Conversation(
            user_id=user_id,
            title=user_message[:50] if len(user_message) > 50 else user_message,
            conversation_mode=conversation_mode,
            api_id=api_id
        )
        db.add(new_conversation)
        db.flush()
        conversation_id = new_conversation.id
    
    user_msg = ChatMessage(
        conversation_id=conversation_id,
        role="user",
        content=user_message
    )
    db.add(user_msg)
    db.flush()
    
    assistant_msg = ChatMessage(
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_message
    )
    db.add(assistant_msg)
    db.flush()
    
    db.commit()
    
    return conversation_id, assistant_msg.id
