import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Загружаем переменные из .env (для безопасности конфигурации)
load_dotenv()

# Получаем URL базы данных из переменных окружения
# Пример: postgresql://user:password@localhost/db_name для PostgreSQL
# Или sqlite:///./test.db для локальной SQLite
DATABASE_URL = os.getenv("DATABASE_URL")

# Создаём engine — объект для управления подключением к БД
# echo=True для логирования SQL-запросов (удобно для отладки, отключите в продакшене)
engine = create_engine(DATABASE_URL, echo=True)

# Настраиваем фабрику сессий: sessionmaker создаёт сессии для работы с БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Функция для dependency injection в FastAPI
# Она предоставляет сессию БД для эндпоинтов и закрывает её после использования
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()