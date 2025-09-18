# Внешние зависимости
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession
import sqlalchemy.orm as so
import sqlalchemy as sa
from datetime import datetime
from typing import List, Optional


class Base(AsyncAttrs, so.DeclarativeBase):
    def update_from_dict(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)              
                
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
        

# Модель Товаров
class Product(Base):
    __tablename__ = "products"
    
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    article: so.Mapped[int] = so.mapped_column(sa.Integer, index=True, unique=True, nullable=False)
    imtId: so.Mapped[int] = so.mapped_column(sa.Integer, unique=True, nullable=False)
    rating_stars: so.Mapped[int] = so.mapped_column(sa.Integer, default=3, nullable=False)
    days_passed:  so.Mapped[int] = so.mapped_column(sa.Integer, default=3, nullable=False)
    
    bad_reviews: so.Mapped[List["BadReview"]] = so.relationship(
        "BadReview", 
        back_populates="product",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f'<Article {self.article}>'
        
    
# Модель плохихи отзывов
class BadReview(Base):
    __tablename__ = "bad_reviews"
    
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    product_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('products.id'))
    rating: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)
    country: so.Mapped[Optional[str]] = so.mapped_column(sa.String(10), nullable=False)
    name: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100), nullable=False)
    text: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False)
    pros: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False)
    cons: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False)
    createdDate: so.Mapped[datetime] = so.mapped_column(sa.DateTime(timezone=True), nullable=False)
    updatedDate: so.Mapped[datetime] = so.mapped_column(sa.DateTime(timezone=True), nullable=False)
    
    # Составной уникальный индекс для предотвращения дубликатов отзывов
    __table_args__ = (
        sa.UniqueConstraint('text', 'pros', 'cons', name='uq_review_content'),
    )
    
    product: so.Mapped["Product"] = so.relationship(
        "Product", 
        back_populates="bad_reviews"
    )
    
    def __repr__(self):
        return f'<id {self.id}>'
    
    
    