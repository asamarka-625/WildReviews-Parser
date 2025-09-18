# Внешние зависимости
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import NoResultFound, SQLAlchemyError, IntegrityError
from fastapi import HTTPException, status
from typing import List, Dict, Any
# Внутренние модули
from app.config import get_config
from app.models import Product, BadReview
from app.database import connection
from app.schemas import BadReviewSchem


config = get_config()


# Получаем отзывы
@connection
async def sql_get_reviews(article: int, session: AsyncSession) -> Dict[str, Any]:
    try:
        product_result = await session.execute(
            sa.select(Product)
            .where(Product.article == article)
            .options(so.selectinload(Product.bad_reviews))
        )
        product = product_result.scalar_one()
        reviews = product.bad_reviews or []
        
        return {
            "article": product.article,
            "imtId": product.imtId,
            "rating_stars": product.rating_stars,
            "days_passed": product.days_passed,
            "reviews_count": len(reviews),
            "reviews": [review.to_dict() for review in reviews]
        }
    
    
    except NoResultFound:
        config.logger.info(f"Product not found for article {article}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading reviews for article {article}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
        
    except Exception as e:
        config.logger.error(f"Unexpected error reading reviews for article {article}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")
        
        
# Записываем отзывы
@connection
async def sql_write_reviews(
    article: int,
    imtId: int,
    rating_stars: int,
    days_passed: int,
    session: AsyncSession,
    reviews: List[BadReviewSchem] = []
) -> List[BadReview]:
    
    try:
        product_result = await session.execute(sa.select(Product).where(Product.article == article))
        product = product_result.scalar_one_or_none()
        
        if product is None:
            product = Product(
                article=article,
                imtId=imtId,
                rating_stars=rating_stars,
                days_passed=days_passed
            )
            
            session.add(product)
            await session.flush() 
                
        else:
            product.imtId = imtId
            product.rating_stars = rating_stars
            product.days_passed = days_passed
            
            # Удаляем старые отзывы
            await session.execute(
                sa.delete(BadReview).where(BadReview.product_id == product.id)
            )
            
        
        if reviews:
            review_values = []
            for data in reviews:
                review_data = data.model_dump()
                review_data["product_id"] = product.id
                review_values.append(review_data)
            
            # Вставка с обработкой конфликтов
            stmt = (
                insert(BadReview)
                .values(review_values)
                .on_conflict_do_nothing(
                    constraint='uq_review_content'
                )
            )
            
            await session.execute(stmt)
            
        await session.commit()
        
        result = await session.execute(sa.select(BadReview).where(BadReview.product_id == product.id))
        return result.scalars().all()
        
    
    except IntegrityError as e:
        config.logger.error(f"Integrity error writing reviews for article {article}: {e}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Database integrity error")
        
    except SQLAlchemyError as e:
        config.logger.error(f"Database error writing reviews for article {article}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
        
    except Exception as e:
        config.logger.error(f"Unexpected error writing reviews for article {article}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")