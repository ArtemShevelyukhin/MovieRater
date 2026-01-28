import json
import os
import urllib

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy import func, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased
from typing import Annotated

from starlette.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi import Request
from starlette.templating import Jinja2Templates

from database import get_db
from models import Movie, Room, User, MoviesInRoom, Rating
from services import get_next_unrated_movie_for_user
from utilites import parse_init_data, get_current_user
from schemas import MovieCreate, RoomCreate, RatingCreate  # создадим схемы ниже
from utilites import get_movie_info_from_kp_url
# from ..dependencies import get_current_user  # пока закомментируем или сделаем заглушку

load_dotenv()  # Уже есть в database.py, но для безопасности
KINO_KREKER = os.getenv("KINO_KREKER")

templates = Jinja2Templates(directory="templates")


rooms = APIRouter(
    prefix="/rooms",
    tags=["rooms"],
    responses={404: {"description": "Not found"}}
)

@rooms.get("/{room_id}")
async def show_room(room_id: str,
                    request: Request,
                    db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)
                    ):
    print('RUN: rooms -> show_room')
    # Получить комнату и проверить членство
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # 2. Получаем последний добавленный фильм через таблицу связи MoviesInRoom
    # Используем join для доступа к дате добавления

    result = get_next_unrated_movie_for_user(db, room_id, user.id)
    if result:
        current_movie, rating = result
    else:
        current_movie, rating = None, None

    # 3. Ищем оценку текущего пользователя (заглушка ID=1, пока нет системы сессий)
    # # В реальном коде используйте user.id из get_current_user
    # rating_obj = db.query(Rating).filter(
    #     Rating.movie_id == current_movie.id,
    #     Rating.user_id == user.id
    # ).first()
    # if rating_obj:
    #     user_rating = rating_obj.score

    return templates.TemplateResponse("room/detail.html", {
        "request": request,
        "room": room,
        "room_id": room.id,
        "current_movie": current_movie,
        "user_rating": rating.score if rating else None
    })


@rooms.get("/")
async def get_rooms(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Если пользователь не зарегестрирован - зарегестрировать (пока что сразу с комнатой)
    TODO: Получить информацию о текущей комнате
    Сделать редирект на главную страницу с текущей комнеатой

    :param request:
    :param db:
    :return:
    """
    # parsed_data = parse_init_data(data.init_data)
    # user_str = parsed_data.get('user')
    # if not user_str:
    #     raise HTTPException(401, "Invalid initData")
    # user_data = json.loads(urllib.parse.unquote(user_str))

    print('RUN: rooms -> get_rooms')
    room = db.query(Room).filter(Room.id == KINO_KREKER).first()
    user.rooms.append(room)
    try:
        db.commit()
        db.refresh(room)
    except IntegrityError:
        db.rollback()  # Откат, чтобы сессия была чистой (ссылка на предыдущее объяснение)

    return JSONResponse({"status": "success", "room_id": room.id})

@rooms.post("/create")
def create_room(room: RoomCreate, db: Session = Depends(get_db)):
    max_attempts = 5  # Ограничение попыток для безопасности
    for attempt in range(max_attempts):
        new_room = Room.create_with_id(name=room.name, is_private=True)  # MVP: private по умолчанию
        db.add(new_room)
        try:
            db.commit()
            db.refresh(new_room)  # Опционально: обновляем объект из БД
            return {"message": "Room created", "room_id": new_room.id}
        except IntegrityError:
            db.rollback()  # Откат, чтобы сессия была чистой (ссылка на предыдущее объяснение)

    # Если все попытки провалились (крайне маловероятно)
    raise HTTPException(status_code=500, detail="Failed to generate unique room ID after multiple attempts")

@rooms.post(
    "/{room_id}/movies",
    # response_model=MovieOut,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить фильм в комнату"
)
async def add_movie_to_room(
    room_id: str,
    create_movie_data: MovieCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    # current_user: Annotated[User, Depends(get_current_user)] = None  # пока можно закомментировать
):
    """
    Добавляет фильм в указанную комнату по kinopoisk_url.

    В MVP предполагаем, что пользователь уже авторизован (потом добавим проверку).
    """
    existing_film = db.query(Movie).filter(Movie.kinopoisk_url == create_movie_data.kinopoisk_url).first()
    if not existing_film:
        new_movie = await get_movie_info_from_kp_url(create_movie_data)
        db.add(new_movie)
        db.flush()
    else:
        new_movie = existing_film

    room = db.query(Room).filter(Room.id == room_id).one_or_none()
    added_by = create_movie_data.added_by if create_movie_data.added_by else user.id
    mv = MoviesInRoom(
        movie_id=new_movie.id,
        room_id=room.id,
        added_by=added_by,
        room=room
    )
    db.add(mv)
    try:
        db.commit()
    except IntegrityError:
        # Если база данных вернула ошибку уникальности (дубликат PK)
        db.rollback()  # Обязательно откатываем транзакцию после ошибки

        # Бросаем 409, чтобы фронтенд показал пользователю "Фильм уже в комнате"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ALREADY_ADDED"
        )
    return new_movie

@rooms.post("/{room_id}/ratings", name="submit_rating")
async def submit_rating(
                    room_id: str,
                    rating_create: RatingCreate,
                    db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)
):
    # Получить комнату и проверить членство
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    existing_rating = db.query(Rating).filter(
        Rating.user_id == user.id,
        Rating.movie_id == rating_create.movie_id
    ).first()

    if existing_rating:
        # Обновляем старую оценку
        existing_rating.score = rating_create.score
    else:
        # Создаем новую запись
        new_rating = Rating(
            user_id=user.id,
            movie_id=rating_create.movie_id,
            score=rating_create.score,
            skipped=False if rating_create.score else True
        )
        db.add(new_rating)

    try:
        db.commit()
    except Exception as e:
        print('!!!', e)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении оценки, {e}")

    result = get_next_unrated_movie_for_user(db, room_id, user.id)
    if result:
        next_movie_in_room, rating = result

        return {
            "status": "success",
            "has_next": True,
            "movie": {
                "id": next_movie_in_room.id,
                "title": next_movie_in_room.title,
                "poster_url": next_movie_in_room.poster_url or "/static/default.jpg"
            }
        }
    else:
        return {
            "status": "success",
            "has_next": False
        }


@rooms.get("/{room_id}/history/", name="get_room_history")
async def get_room_history(
                    room_id: str,
                    request: Request,
                    sort_by: str = "date",
                    db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)
):
    print('RUN: rooms -> get_room_history')

    my_rating_alias = aliased(Rating)

    query = db.query(
        Movie,
        MoviesInRoom.added_date,
        User.username.label("added_by_name"),
        func.avg(Rating.score).label("avg_score")
    ).join(MoviesInRoom, Movie.id == MoviesInRoom.movie_id) \
        .join(User, MoviesInRoom.added_by == User.id) \
        .outerjoin(Rating, Movie.id == Rating.movie_id) \
        .filter(MoviesInRoom.room_id == room_id) \
        .group_by(Movie.id, MoviesInRoom.added_date, User.username)

    # Логика сортировки
    if sort_by == "my_rating":
        # Сложная сортировка: нужно джойнить оценки текущего пользователя
        # Чтобы отсортировать по "моей" оценке, нужно приджойнить оценки текущего юзера
        query = query.outerjoin(
            my_rating_alias,
            and_(Movie.id == my_rating_alias.movie_id, my_rating_alias.user_id == user.id)
        ).order_by(my_rating_alias.score.desc().nulls_last())
    elif sort_by == "avg_rating":
        query = query.order_by(func.avg(Rating.score).desc().nulls_last())
    else:
        query = query.order_by(MoviesInRoom.added_date.desc())

    movies_data = query.all()

    history_list = []
    for m, added_date, added_by_name, avg_score in movies_data:
        # Получаем оценку текущего пользователя
        my_rating = db.query(Rating.score).filter(
            Rating.movie_id == m.id,
            Rating.user_id == user.id
        ).scalar()

        # Получаем все оценки для попапа
        all_ratings = (db.query(User.username, Rating.score)
                       .join(User)
                       .filter(Rating.movie_id == m.id)
                       .order_by(Rating.score.desc())
                       .all())

        history_list.append({
            "movie": m,
            "added_date": added_date.strftime("%d.%m.%Y"),
            "added_by": added_by_name,
            "avg_score": round(avg_score, 2) if avg_score else 0,
            "my_score": my_rating or "-",
            "details": [{"name": r[0], "score": r[1]} for r in all_ratings]
        })

    return templates.TemplateResponse("room/history.html", {
        "request": request,
        "history": history_list,
        "room_id": room_id,
        "current_sort": sort_by
    })

