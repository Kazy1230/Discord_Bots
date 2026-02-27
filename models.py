from sqlalchemy import DateTime, Integer, create_engine, Column, String, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

class UserStat(Base):
    __tablename__ = "score_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    amount = Column(BigInteger, nullable=False)
    created_at = Column(DateTime)
    server = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

