from sqlalchemy import create_engine
from sqlalchemy.exc.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

url_database = "sqlite:///./converter.db"

engine = create_engine(url_database, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocmmit=False, autoflush=False, bind=engine)

Base = declarative_base()
