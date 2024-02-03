from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, TIMESTAMP
from database import Base
import datetime
from sqlalchemy.orm import relationship


class Questions(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(String, index=True)


class Choices(Base):
    __tablename__ = "choices"

    id = Column(Integer, primary_key=True, index=True)
    choice_text = Column(String, index=True)
    is_correct = Column(Boolean, default=False)
    q_id = Column(Integer, ForeignKey("questions.id"))


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_pw = Column(String)
    subdomain = Column(String, unique=True, index=True)
    apikey = Column(String, unique=True, index=True)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    tries = Column(Integer, default=3)

    chats = relationship('Chats', backref='user', cascade='all, delete')


class Chats(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(Integer, ForeignKey("users.id"), )
    chatname = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    messages = relationship('Messages', backref='chat', cascade='all, delete')



class Messages(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cid = Column(Integer, ForeignKey("chats.id"))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)

    role = Column(String)
    message_text = Column(String)
