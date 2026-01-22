from sqlalchemy import create_engine, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, declarative_base, sessionmaker
from sqlalchemy.exc import IntegrityError

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)  # Автоинкрементный ID
    telegram_id: Mapped[str] = mapped_column(String, unique=True)  # Уникальный Telegram ID
    username: Mapped[str] = mapped_column(String)  # Имя пользователя (не уникальное)

# Пример создания БД и сессии (для теста)
engine = create_engine('sqlite:///:memory:')  # В памяти для примера; в проекте используй PostgreSQL
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Добавляем пользователя
user1 = User(telegram_id='12345', username='user_one')
session.add(user1)
session.commit()  # Успех

# Пытаемся добавить дубликат
try:
    user2 = User(telegram_id='12345', username='user_two')  # Тот же telegram_id
    a = session.query(User).filter_by(telegram_id='12345').first()
    session.add(user2)
    session.commit()
except IntegrityError as e:
    session.rollback()  # Откат, если ошибка
    print(f"Ошибка: {e}")  # Вывод: UNIQUE constraint failed: users.telegram_id