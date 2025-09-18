# Внешние зависимости
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import conint
from typing import List
# Внутренние модули
from app.schemas import RequestReviewSchem, BadReviewResponse
from app.models import BadReview
from app.parser import parser_run
from app.crud import sql_get_reviews, sql_write_reviews


router = APIRouter()


# Выводим отзывывы по article из БД
@router.get("/api/v1/reviews/{article}", response_class=JSONResponse)
async def get_reviews(article: conint(ge=0)):
    result = await sql_get_reviews(article=article)
    
    return result


# Папрсим и записываем отзывы в БД
@router.post("/api/v1/parse/", response_model=List[BadReviewResponse])
async def parse_reviews(data: RequestReviewSchem):
    imtId, result = await parser_run(**data.model_dump())
    
    reviews = await sql_write_reviews(
        article=data.article,
        imtId=imtId,
        rating_stars=data.rating_stars,
        days_passed=data.days_passed,
        reviews=result
    )
    
    return reviews
    
        
        
    
    