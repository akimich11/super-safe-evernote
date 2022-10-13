from datetime import datetime

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from fastapi_users_db_sqlalchemy.generics import GUID
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Note(Base):
    __tablename__ = "note"

    id = Column(Integer, primary_key=True)
    user_id = Column(GUID, ForeignKey("user.id"))
    name = Column(String, unique=True)
    message = Column(String)


class User(SQLAlchemyBaseUserTableUUID, Base):
    notes = relationship(Note, backref="user")
    public_key = Column(String)
    pk_updated_at = Column(DateTime, onupdate=datetime.now)
