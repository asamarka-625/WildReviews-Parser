# WildReviews Parser

Микросервис для парсинга и хранения отзывов с Wildberries по артикулам товаров. Запускается через Docker Compose.

## 🚀 Возможности

- Парсинг отзывов с Wildberries по артикулу товара
- Хранение отзывов в базе данных PostgreSQL
- Сохранение отзывов в базе данных по рейтингу и дате
- RESTful API для доступа к данным
- Автоматическое предотвращение дубликатов отзывов
- Полная контейнеризация с Docker

## 📦 Установка

### Требования

- Docker 20.10+
- Docker Compose 2.0+

### Быстрый запуск

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/asamarka-625/WildReviews-Parser.git
cd WildReviews-Parser
```

2. **Настройка окружения:**
```
Отредактируйте .env с вашими настройками:

# .env
POSTGRES_DB=diary_db
POSTGRES_USER=diary_user
POSTGRES_PASSWORD=diary_password
```

3. **Запуск с Docker Compose:**
```
# Сборка и запуск контейнеров
docker compose up --build

# Запуск в фоновом режиме
docker compose up -d

# Остановка контейнеров
docker compose down
```

4. **Доступ к приложению:**
```
После запуска приложение будет доступно по адресу:

- API Documentation: http://localhost:8000/docs
```

5. **Просмотр логов:**
```
docker compose logs -f web
docker compose logs -f db
```

## 📡 API Endpoints

### 🔍 Получение отзывов по артикулу
- **GET api/v1/reviews/{article}** - Получить отзывы из БД

### ➕ Парсинг и сохранение отзывов
- **POST api/v1/parse/** - Парсинг и сохранение отзывов

### Пример:
```
curl -X POST "http://localhost:8000/api/v1/parse/" \
  -H "Content-Type: application/json" \
  -d '{"article": 261401756, "rating_stars": 3, "days_passed": 7}'
```