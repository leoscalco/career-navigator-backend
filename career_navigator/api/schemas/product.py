from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from career_navigator.domain.models.product_type import ProductType


class ProductCreate(BaseModel):
    user_id: int
    product_type: ProductType
    content: Optional[Dict[str, Any]] = None
    version: int = 1
    is_active: bool = True
    generated_at: Optional[datetime] = None
    model_used: Optional[str] = None
    prompt_used: Optional[str] = None


class ProductUpdate(BaseModel):
    product_type: Optional[ProductType] = None
    content: Optional[Dict[str, Any]] = None
    version: Optional[int] = None
    is_active: Optional[bool] = None
    generated_at: Optional[datetime] = None
    model_used: Optional[str] = None
    prompt_used: Optional[str] = None


class ProductResponse(BaseModel):
    id: int
    user_id: int
    product_type: ProductType
    content: Optional[Dict[str, Any]]
    version: int
    is_active: bool
    generated_at: Optional[datetime]
    model_used: Optional[str]
    prompt_used: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

