from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

engine = None
SessionLocal = None
Base = declarative_base()

def init_db(database_url):
    global engine, SessionLocal
    engine = create_engine(database_url, pool_pre_ping=True, pool_recycle=3600)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
