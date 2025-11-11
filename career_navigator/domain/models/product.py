from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from career_navigator.domain.models.product_type import ProductType


class GeneratedProduct(BaseModel):
    id: Optional[int] = None
    user_id: int
    product_type: ProductType
    content: Optional[Dict[str, Any]] = None
    version: int = 1
    is_active: bool = True
    generated_at: Optional[datetime] = None
    model_used: Optional[str] = None
    prompt_used: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

