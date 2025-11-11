from abc import ABC, abstractmethod
from typing import List, Optional
from career_navigator.domain.models.product import GeneratedProduct
from career_navigator.domain.models.product_type import ProductType


class ProductRepository(ABC):
    @abstractmethod
    def create(self, product: GeneratedProduct) -> GeneratedProduct:
        """Create a new generated product."""
        pass

    @abstractmethod
    def get_by_id(self, product_id: int) -> Optional[GeneratedProduct]:
        """Get product by ID."""
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> List[GeneratedProduct]:
        """Get all products for a user."""
        pass

    @abstractmethod
    def get_by_user_and_type(
        self, user_id: int, product_type: ProductType
    ) -> List[GeneratedProduct]:
        """Get products by user ID and product type."""
        pass

    @abstractmethod
    def get_all(self) -> List[GeneratedProduct]:
        """Get all products."""
        pass

    @abstractmethod
    def update(self, product: GeneratedProduct) -> GeneratedProduct:
        """Update an existing product."""
        pass

    @abstractmethod
    def delete(self, product_id: int) -> bool:
        """Delete a product by ID."""
        pass

