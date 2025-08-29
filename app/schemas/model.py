from pydantic import BaseModel
from typing import List

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
