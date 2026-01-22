from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from models import Base, User, Room, Movie, Rating, MoviesInRoom
from datetime import datetime

# 1. Настройка временной БД в памяти
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)

with Session(engine) as session:
    print("--- Тест: Создание данных ---")

    # 2. Создаем комнату (используем твой метод создания с nanoid)
    #
    new_room = Room.create_with_id(name="Киноманы 2026")
    session.add(new_room)
    session.flush()  # Получаем ID комнаты для дальнейшего использования
    print(f"Создана комната: {new_room.name} (ID: {new_room.id})")

    # 3. Создаем пользователя
    #
    user = User(telegram_id="12345678", username="ivan_pro", current_room=new_room.id)
    user.rooms.append(new_room)  # Добавляем пользователя в комнату через many-to-many связь
    session.add(user)
    print(f"Создан пользователь: {user.username}")

    # 4. Создаем фильм
    #
    movie = Movie(
        title="Inception",
        year=2010,
        kinopoisk_id=447301,
        kinopoisk_url="https://kinopoisk.ru/film/447301/"
    )
    session.add(movie)
    session.flush()

    # 5. Добавляем фильм в комнату (через связующую таблицу)
    #
    link = MoviesInRoom(movie_id=movie.id, room_id=new_room.id, added_by=user.id)
    session.add(link)
    print(f"Фильм '{movie.title}' добавлен в комнату.")

    # 6. Выставляем оценку (тестируем составной ключ из твоего вопроса)
    rating = Rating(user_id=user.id, movie_id=movie.id, score=8.5)
    session.add(rating)
    session.commit()
    print(f"Оценка {rating.score} сохранена.")

    print("\n--- Тест: Проверка связей (Relationships) ---")

    # Проверяем, видит ли SQLAlchemy объекты через relationship
    test_rating = session.get(Rating, (user.id, movie.id))
    print(f"Рейтинг найден. Фильм: {test_rating.movie.title}, Пользователь: {test_rating.user.username}")

    # Проверяем список участников комнаты
    current_room = session.get(Room, new_room.id)
    print(f"Участники комнаты '{current_room.name}': {[u.username for u in current_room.members]}")
