from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from career_navigator.infrastructure.database.session import get_db
from career_navigator.infrastructure.repositories.product_repository import SQLAlchemyProductRepository
from career_navigator.domain.models.product import GeneratedProduct as DomainProduct
from career_navigator.domain.models.product_type import ProductType
from career_navigator.api.schemas.product import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter(prefix="/products", tags=["Generated Products"])


def get_product_repository(db: Session = Depends(get_db)) -> SQLAlchemyProductRepository:
    """Dependency to get product repository."""
    return SQLAlchemyProductRepository(db)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_data: ProductCreate,
    repository: SQLAlchemyProductRepository = Depends(get_product_repository),
):
    """Create a new generated product."""
    domain_product = DomainProduct(**product_data.model_dump())
    created_product = repository.create(domain_product)
    return ProductResponse.model_validate(created_product)


@router.get("", response_model=List[ProductResponse])
def get_all_products(
    repository: SQLAlchemyProductRepository = Depends(get_product_repository),
):
    """Get all generated products."""
    products = repository.get_all()
    return [ProductResponse.model_validate(p) for p in products]


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    repository: SQLAlchemyProductRepository = Depends(get_product_repository),
):
    """Get a product by ID."""
    product = repository.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )
    return ProductResponse.model_validate(product)


@router.get("/user/{user_id}", response_model=List[ProductResponse])
def get_products_by_user(
    user_id: int,
    product_type: Optional[ProductType] = Query(None, description="Filter by product type"),
    repository: SQLAlchemyProductRepository = Depends(get_product_repository),
):
    """Get all products for a user, optionally filtered by type."""
    if product_type:
        products = repository.get_by_user_and_type(user_id, product_type)
    else:
        products = repository.get_by_user_id(user_id)
    return [ProductResponse.model_validate(p) for p in products]


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    repository: SQLAlchemyProductRepository = Depends(get_product_repository),
):
    """Update a product."""
    existing_product = repository.get_by_id(product_id)
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )
    
    # Update only provided fields
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_product, field, value)
    
    updated_product = repository.update(existing_product)
    return ProductResponse.model_validate(updated_product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    repository: SQLAlchemyProductRepository = Depends(get_product_repository),
):
    """Delete a product."""
    success = repository.delete(product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )

