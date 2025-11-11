from typing import List, Optional
from sqlalchemy.orm import Session
from career_navigator.domain.repositories.product_repository import ProductRepository
from career_navigator.domain.models.product import GeneratedProduct as DomainProduct
from career_navigator.domain.models.product_type import ProductType
from career_navigator.infrastructure.database.models import GeneratedProduct as DBProduct


class SQLAlchemyProductRepository(ProductRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, product: DomainProduct) -> DomainProduct:
        db_product = DBProduct(
            user_id=product.user_id,
            product_type=product.product_type.value,
            content=product.content,
            version=product.version,
            is_active=product.is_active,
            generated_at=product.generated_at,
            model_used=product.model_used,
            prompt_used=product.prompt_used,
        )
        self.db.add(db_product)
        self.db.commit()
        self.db.refresh(db_product)
        return self._to_domain(db_product)

    def get_by_id(self, product_id: int) -> Optional[DomainProduct]:
        db_product = self.db.query(DBProduct).filter(DBProduct.id == product_id).first()
        return self._to_domain(db_product) if db_product else None

    def get_by_user_id(self, user_id: int) -> List[DomainProduct]:
        db_products = self.db.query(DBProduct).filter(DBProduct.user_id == user_id).all()
        return [self._to_domain(p) for p in db_products]

    def get_by_user_and_type(
        self, user_id: int, product_type: ProductType
    ) -> List[DomainProduct]:
        db_products = self.db.query(DBProduct).filter(
            DBProduct.user_id == user_id,
            DBProduct.product_type == product_type.value
        ).all()
        return [self._to_domain(p) for p in db_products]

    def get_all(self) -> List[DomainProduct]:
        db_products = self.db.query(DBProduct).all()
        return [self._to_domain(p) for p in db_products]

    def update(self, product: DomainProduct) -> DomainProduct:
        db_product = self.db.query(DBProduct).filter(DBProduct.id == product.id).first()
        if not db_product:
            raise ValueError(f"Product with id {product.id} not found")
        
        db_product.product_type = product.product_type.value
        db_product.content = product.content
        db_product.version = product.version
        db_product.is_active = product.is_active
        db_product.generated_at = product.generated_at
        db_product.model_used = product.model_used
        db_product.prompt_used = product.prompt_used
        
        self.db.commit()
        self.db.refresh(db_product)
        return self._to_domain(db_product)

    def delete(self, product_id: int) -> bool:
        db_product = self.db.query(DBProduct).filter(DBProduct.id == product_id).first()
        if not db_product:
            return False
        
        self.db.delete(db_product)
        self.db.commit()
        return True

    def _to_domain(self, db_product: DBProduct) -> DomainProduct:
        return DomainProduct(
            id=db_product.id,
            user_id=db_product.user_id,
            product_type=ProductType(db_product.product_type),
            content=db_product.content,
            version=db_product.version,
            is_active=db_product.is_active,
            generated_at=db_product.generated_at,
            model_used=db_product.model_used,
            prompt_used=db_product.prompt_used,
            created_at=db_product.created_at,
            updated_at=db_product.updated_at,
        )

