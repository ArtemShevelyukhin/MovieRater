from sqlalchemy.orm import Session
from models import Movie, MoviesInRoom, Rating

def get_next_unrated_movie_for_user(db: Session, room_id: str, user_id: int) -> Movie | None:
    """
    Чистая бизнес-логика: найти фильм, который пользователь еще не видел.
    """
    return db.query(Movie, Rating) \
             .outerjoin(Rating, (Rating.user_id == user_id) & (Rating.movie_id == Movie.id)) \
             .join(MoviesInRoom) \
             .filter(MoviesInRoom.room_id == room_id) \
             .filter(Rating.score.is_(None)) \
             .order_by(MoviesInRoom.added_date.asc()) \
             .first()