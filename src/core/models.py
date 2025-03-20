# from sqlalchemy.orm import Mapped, mapped_column
# from database import Base, async_session_factory, async_engine

# class User(Base):
#     __tablename__ = "users"

#     id: Mapped[int] = mapped_column(primary_key=True)
#     username: Mapped[str] 

# def create_tables():
#     Base.metadata.drop_all(async_engine)
#     Base.metadata.create_all(async_engine)

# async def insert_data():
#     user1 = User(username = "Alex")
#     async with async_session_factory() as session:
#         session.add(user1)
#         await session.commit()