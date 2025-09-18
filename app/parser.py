# Внешние зависимости
import httpx
from fastapi import HTTPException, status
from typing import List, Tuple
from datetime import datetime, timezone, timedelta
# Внутренние модули
from app.config import get_config
from app.schemas import BadReviewSchem


config = get_config()


# Получает imtId по артикулу товара
async def get_imtid_from_nmid(nm_id: int) -> int:
    url = f"https://u-card.wb.ru/cards/v4/detail?appType=1&curr=rub&dest=-1185367&spp=30&ab_testing=false&lang=ru&nm={nm_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': f'https://www.wildberries.ru/catalog/{nm_id}/detail.aspx'
    }
    
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
                timeout=10
            )
        
            response.raise_for_status()
            data = response.json()
            
            if not data or not isinstance(data, dict):
                config.logger.warning(f"Invalid API response structure for nm_id {nm_id}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Invalid response from Wildberries API"
                )
            
            products = data.get('products', [])
            if not products:
                config.logger.info(f"Product not found for nm_id {nm_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
            
            imt_id = products[0].get('root')
            if not imt_id:
                config.logger.warning(f"imtId not found in product data for nm_id {nm_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="imtId not found for this product"
                )
                
            config.logger.debug(f"Successfully got imtId {imt_id} for nm_id {nm_id}")
            
            return imt_id
      
      
    except httpx.TimeoutException:
        config.logger.warning(f"Timeout while fetching imtId for nm_id {nm_id}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request to Wildberries timed out"
        )
        
    except httpx.HTTPStatusError as e:
        config.logger.error(f"HTTP error {e.response.status_code} for nm_id {nm_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Wildberries API returned error"
        )
        
    except httpx.RequestError as e:
        config.logger.error(f"Network error for nm_id {nm_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Network error connecting to Wildberries"
        )
        
    except ValueError as e:
        config.logger.error(f"JSON parsing error for nm_id {nm_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid JSON response from Wildberries"
        )
    
    except HTTPException as e:
        raise e
        
    except Exception as e:
        config.logger.error(f"Unexpected error getting imtId for nm_id {nm_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error"
        )
        

# Получает необработанные отзывы по imtId
async def get_raw_reviews_from_imtid(nm_id: int, imtId: int) -> List[dict]:
    feedback_servers = [
        f"https://feedbacks1.wb.ru/feedbacks/v2/{imtId}",
        f"https://feedbacks2.wb.ru/feedbacks/v2/{imtId}",
        f"https://feedbacks1.wb.ru/feedbacks/v1/{imtId}",
        f"https://feedbacks2.wb.ru/feedbacks/v1/{imtId}"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': f'https://www.wildberries.ru/catalog/{nm_id}/detail.aspx'
    }
    
    for url in feedback_servers:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=headers,
                    timeout=10
                )
            
                response.raise_for_status()
                data = response.json()
                
                raw_reviews = data.get("feedbacks")
                
                if raw_reviews is None:
                    continue
                    
                return raw_reviews or []
          
          
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                config.logger.info(f"No reviews found for imt_id {imt_id}")
                return []
            
            config.logger.error(f"HTTP error {e.response.status_code} for imt_id {nm_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Wildberries API returned error"
            )
            
        except httpx.TimeoutException:
            config.logger.warning(f"Timeout while fetching reviews for nm_id {nm_id}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Request to Wildberries timed out"
            )
            
        except httpx.RequestError as e:
            config.logger.error(f"Network error fetching reviews for nm_id {nm_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Network error connecting to Wildberries"
            )
            
        except ValueError as e:
            config.logger.error(f"JSON parsing error getting reviews for nm_id {nm_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid JSON response from Wildberries"
            )
        
        except HTTPException as e:
            raise e
            
        except Exception as e:
            config.logger.error(f"Unexpected error getting reviews for nm_id {nm_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected server error"
            )
        

# Обрабатывает и фильтрует отзывы
def pasrse_reviews(raw_reviews: List[dict], rating_stars: int = 3, days_passed: int = 3) -> List[BadReviewSchem]:
    reviews = []
    
    for data in raw_reviews:
        rating = data.get("productValuation")
        
        if not rating or not isinstance(rating, int) or rating >= rating_stars:
            continue
        
        user_data = data.get("wbUserDetails", {})
        createdDate = datetime.strptime(data["createdDate"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        updatedDate = datetime.strptime(data["updatedDate"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        
        if datetime.now(timezone.utc)- updatedDate > timedelta(days=days_passed):
            continue
            
        try:
            review = BadReviewSchem(
                rating=rating,
                country=user_data["country"].upper() if user_data.get("country") else None,
                name=user_data.get("name"),
                text=data.get("text"),
                pros=data.get("pros"),
                cons=data.get("cons"),
                createdDate=createdDate,
                updatedDate=updatedDate
            )
        
        except:
            continue
        
        else:
            reviews.append(review)
            
    return reviews
    

# Запускает парсер
async def parser_run(article: int, rating_stars: int = 3, days_passed: int = 3) -> Tuple[int, List[BadReviewSchem]]:
    imtId = await get_imtid_from_nmid(article)
    raw_reviews = await get_raw_reviews_from_imtid(nm_id=article, imtId=imtId)
    
    reviews = pasrse_reviews(raw_reviews=raw_reviews, rating_stars=rating_stars, days_passed=days_passed)
    
    return imtId, reviews