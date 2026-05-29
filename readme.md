
# Асинхронный микросервис для обработки платежей с гарантированной доставкой событий через Outbox pattern и RabbitMQ.

## Архитектура
```
Payment_Service/
│
├── .env.example                    # Пример переменных окружения
├── .gitignore                      # Git ignore файл
├── docker-compose.yml              # Docker Compose конфигурация
├── Dockerfile                      # Docker образ для сервиса
├── README.md                       # Полная документация проекта
├── requirements.txt                # Продакшен зависимости
├── alembic.ini                     # Конфигурация Alembic миграций
│
├── app/                            # Основной код приложения
│   ├── __init__.py
│   ├── main.py                     # FastAPI приложение (точка входа API)
│   │
│   ├── api/                        # API слой
│   │   ├── __init__.py
│   │   └──
│   │   └── payments.py             # Эндпоинты: POST /payments, GET /payments/{id}
│   │
│   ├── core/                       # Ядро приложения
│   │   ├── __init__.py
│   │   ├── config.py               # Конфигурация (чтение .env)
│   │   └── database.py             # Подключение к БД, сессии, engine
│   │
│   ├── models/                     # SQLAlchemy модели (ORM)
│   │   ├── __init__.py
│   │   ├── payment.py              # Модель Payment (таблица payments)
│   │   └── outbox.py               # Модель OutboxEvent (таблица outbox)
│   │
│   ├── schemas/                    # Pydantic схемы (валидация)
│   │   ├── __init__.py
│   │   └── payment.py              # Request/Response схемы для API
│   │
│   ├── services/                   # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── payment_actions.py      # CRUD операции с платежами
│   │   ├── outbox_actions.py       # Работа с outbox событиями
│   │   ├── payment_gateway.py      # Эмуляция внешнего шлюза (2-5 сек, 90% успех)
│   │   ├── webhook_sender.py       # Отправка webhook с retry (3 попытки)
│   │   └── event_publisher.py      # Публикация событий в RabbitMQ
│   │
│   ├── consumers/                  # RabbitMQ consumers
│   │   ├── __init__.py
│   │   └── payment_consumer.py     # Обработка платежей из очереди
│   │
│   ├── workers/                    # Background workers
│   │   ├── __init__.py
│   │   └── outbox_worker.py        # Периодическая отправка outbox событий
│   │
│   └── middleware/                 # FastAPI middleware
│       ├── __init__.py
│       └── auth.py                 # API Key аутентификация
│
├── migrations/                     # Alembic миграции БД
│   ├── env.py                      # Настройка окружения для миграций
│   ├── script.py.mako              # Шаблон для новых миграций
│   └── versions/                   # Файлы миграций
│       ├── 001_create_payments_table.py
│       └── 002_create_outbox_table.py
│
├── scripts/                        # Вспомогательные скрипты
│   ├── run_worker.py               # Запуск outbox worker
│   ├── run_consumer.py             # Запуск payment consumer
│   └── health_check.py             # Проверка состояния сервисов
```

## Технологии

- **FastAPI** + Pydantic v2 - API фреймворк
- **SQLAlchemy 2.0** (асинхронный) - ORM
- **PostgreSQL** - основная БД
- **RabbitMQ** - брокер сообщений
- **Alembic** - миграции
- **Docker** + docker-compose - контейнеризация

## Функциональность

-  Создание платежа с идемпотентностью (Idempotency-Key)
-  Получение информации о платеже
-  Outbox pattern для гарантированной доставки
-  Асинхронная обработка через RabbitMQ
-  Эмуляция платежного шлюза (2-5 сек, 90% успех)
-  Webhook уведомления с retry (3 попытки)
-  Dead Letter Queue для упавших сообщений
-  API Key аутентификация
-  Docker Compose для всех сервисов

## Быстрый старт

### Предварительные требования
- Docker и Docker Compose
- Python 3.12+ (для локальной разработки)


## Запуск с Docker

# 1. **Клонируйте репозиторий**
```bash
git clone <repository-url>
cd payment-service
```

## 2. **Запустите все сервисы**: 
```bash
docker-compose up --build
```
Проверьте работу сервисов

# Health check
```
curl http://localhost:8000/health
```

# Создание платежа
```
curl -X POST http://localhost:8000/api/v1/payments/ \
  -H "X-API-Key: test-api-key-123" \
  -H "Idempotency-Key: unique-key-001" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 100.50,
    "currency": "USD",
    "description": "Test payment",
    "metadata": {"order_id": "12345"},
    "webhook_url": "https://webhook.site/your-test-id"
  }'
```

## Локальная разработка

1. Создайте виртуальное окружение
```
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows
```

2. Установите зависимости
```
pip install -r requirements.txt
pip install -r requirements-test.txt
```

3. Запустите инфраструктуру
```
docker-compose up -d postgres rabbitmq
```

4. Примените миграции
```
alembic upgrade head
```

5. Запустите сервисы в разных терминалах
```
# Терминал 1: API сервер
uvicorn app.main:app --reload --port 8000

# Терминал 2: Outbox worker
python scripts/run_worker.py

# Терминал 3: Payment consumer
python scripts/run_consumer.py
```

## Аутентификация

Все запросы к API требуют заголовок X-API-Key:

X-API-Key: test-api-key-123

## Эндпоинты

1. Создание платежа
```
POST /api/payments
```
### Заголовки:

    X-API-Key: API ключ (обязательный)

    Idempotency-Key: Уникальный ключ для защиты от дублей (обязательный)


## Тело запроса:
```
{
  "amount": 100.50,
  "currency": "USD",
  "description": "Purchase description",
  "meta_data": {
    "product_id": "prod-123",
    "quantity": 2
  },
  "webhook_url": "https://example.com/webhook"
}
```
## Ответ (202 Accepted):
```
{
  "payment_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z"
}
```
## Получение информации о платеже
```
GET /api/payments/{payment_id}
```
## Ответ (200 OK):
```
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "idempotency_key": "unique-key-001",
  "amount": 100.50,
  "currency": "USD",
  "description": "Purchase description",
  "meta_data": {"product_id": "prod-123"},
  "status": "succeeded",
  "webhook_url": "https://example.com/webhook",
  "created_at": "2024-01-15T10:30:00Z",
  "processed_at": "2024-01-15T10:30:05Z"
}
```