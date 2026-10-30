import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DATABASE_USERNAME = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_PORT = int(os.getenv("DATABASE_PORT", "5432"))

database_url = URL.create(
    drivername="postgresql+psycopg2",
    username=DATABASE_USERNAME,
    password=DATABASE_PASSWORD,
    host=DATABASE_HOST,
    port=DATABASE_PORT,
    database=DATABASE_NAME,
)

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()