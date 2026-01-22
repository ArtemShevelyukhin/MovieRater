from typing import List, Optional
from sqlalchemy import ForeignKey, Integer, create_mock_engine, create_engine
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship, Session


# 1. Определение моделей (согласно твоему коду)
class Base(DeclarativeBase):
    pass


class Association(Base):
    __tablename__ = "association_table"
    left_id: Mapped[int] = mapped_column(ForeignKey("left_table.id"), primary_key=True)
    right_id: Mapped[int] = mapped_column(ForeignKey("right_table.id"), primary_key=True)

    # Дополнительные данные в связи
    extra_data: Mapped[Optional[str]] = mapped_column()

    # Ссылка на объект Child для удобного доступа
    child: Mapped["Child"] = relationship(back_populates="parents")
    # Ссылка на объект Parent для обратной связи
    parent: Mapped["Parent"] = relationship(back_populates="children")


class Parent(Base):
    __tablename__ = "left_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()  # Добавим для наглядности

    # Связь идет к Association, а не напрямую к Child
    children: Mapped[List["Association"]] = relationship(back_populates="parent")


class Child(Base):
    __tablename__ = "right_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()  # Добавим для наглядности

    parents: Mapped[List["Association"]] = relationship(back_populates="child")


# 2. Настройка базы данных и наполнение данными
def run_example():
    # Используем SQLite в памяти для тестов
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        # Создаем объекты Parent и Child
        p1 = Parent(id=1, name="Родитель А")
        c1 = Child(id=1, name="Ребенок 1")
        c2 = Child(id=2, name="Ребенок 2")

        # Создаем связи через объект Association
        # Здесь мы записываем extra_data
        assoc1 = Association(extra_data="Первенец", child=c1)
        assoc2 = Association(extra_data="Второй ребенок", child=c2)

        # Добавляем ассоциации к родителю
        p1.children.append(assoc1)
        p1.children.append(assoc2)

        session.add(p1)
        session.commit()

        # 3. Демонстрация работы
        print(f"--- Исследование объекта Parent (ID: {p1.id}) ---")
        # Чтобы добраться до ребенка, нужно пройти через объект Association
        for assoc in p1.children:
            print(f"Связь найдена: {assoc.parent.name} -> {assoc.child.name}")
            print(f"Дополнительные данные из связи: {assoc.extra_data}")
            print("-" * 10)


if __name__ == "__main__":
    run_example()