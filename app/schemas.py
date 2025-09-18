# Внешние зависимости
from pydantic import BaseModel, constr, conint
from datetime import datetime
from typing import Optional


# Схема запроса для парсинага отзывов
class RequestReviewSchem(BaseModel):
    article: conint(ge=0)
    rating_stars: conint(ge=0, le=6) = 3
    days_passed: conint(ge=0) = 3
    

class BadReviewResponse(BaseModel):
    id: conint(ge=1)
    product_id: conint(ge=0)
    rating: conint(ge=0)
    country: Optional[constr(min_length=1, max_length=10)]
    name: Optional[constr(min_length=1, max_length=100)]
    text: str
    pros: str
    cons: str
    createdDate: datetime
    updatedDate: datetime

    class Config:
        from_attributes = True
        
        
# Схема отзывов
class BadReviewSchem(BaseModel):
    rating: conint(ge=0)
    country: Optional[constr(min_length=1, max_length=10)]
    name: Optional[constr(min_length=1, max_length=100)]
    text: constr(strip_whitespace=True)
    pros: constr(strip_whitespace=True)
    cons: constr(strip_whitespace=True)
    createdDate: datetime
    updatedDate: datetime
    
    class Config:
        from_attributes = True