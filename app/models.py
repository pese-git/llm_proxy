from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class MessageRole(str, Enum):
    system = "system"
    user = "user"
    assistant = "assistant"
    developer = "developer"  # Поддержка роли developer от Void IDE
    tool = "tool"  # Поддержка роли tool от Void IDE
    function = "function"  # Поддержка роли function (для обратной совместимости)

class Message(BaseModel):
    role: MessageRole
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "gpt-3.5-turbo"
    messages: List[Message]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[List[str]] = None
    presence_penalty: Optional[float] = 0
    frequency_penalty: Optional[float] = 0
    user: Optional[str] = None

class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: str

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_cost: float
    completion_cost: float
    total_cost: float

class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
    usage: Usage



class ModelInfo(BaseModel):
    id: str
    object: str
    created: int
    title: str
    max_capacity: int
    cost_context: str
    cost_completion: str

class ModelsResponse(BaseModel):
    object: str
    data: List[ModelInfo]