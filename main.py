from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated, List
import json

import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session

from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from gpt_handlers import generate_gpt, get_ticket_requirement
from zenpy_handlers import get_all_tickets

from utilities.validators import validate_email
from utilities.model_to_dict import user_to_dict
from Exceptions import (
    UNAUTHORIZED,
    EMAIL_CONFLICT,
    USERNAME_CONFLICT,
    EMAIL_INVALID,
    NOT_FOUND,
    CREDENTIALS_NEEDED,
    BAD_REQUEST,
)

from Bases import (
    ChoiceBase,
    QuestionBase,
    UserBase,
    UserCreationBase,
    Token,
    TokenData,
    ZendeskCredsBase,
    GPTQuestionBase,
    MessageBase,
)

from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES"))
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "https://zendai-frotend-m-haris-n.vercel.app",
]

oauth_2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


def create_access_token(data: dict, expires_delta: timedelta or None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta

    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(db: db_dependency, token: str = Depends(oauth_2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise UNAUTHORIZED

        token_data = TokenData(username=username)

    except JWTError:
        raise UNAUTHORIZED

    user = (
        db.query(models.Users)
        .filter(models.Users.username == token_data.username)
        .first()
    )
    if user is None:
        raise UNAUTHORIZED

    userdict = user.__dict__.copy()
    del userdict["hashed_pw"]

    return userdict


# USER ROUTES


@app.post("/register/")
async def create_user(userinfo: UserCreationBase, db: db_dependency):
    email_in_use = (
        db.query(models.Users).filter(models.Users.email == userinfo.email).first()
    )
    username_in_use = (
        db.query(models.Users)
        .filter(models.Users.username == userinfo.username)
        .first()
    )
    email_valid = validate_email(userinfo.email)
    if email_in_use:
        raise EMAIL_CONFLICT
    if username_in_use:
        raise USERNAME_CONFLICT
    if not email_valid:
        raise EMAIL_INVALID

    user = models.Users(
        username=userinfo.username,
        email=userinfo.email,
        hashed_pw=pwd_context.hash(userinfo.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        "status": 200,
        "data": {
            "username": userinfo.username,
            "email": userinfo.email,
        },
    }


@app.post("/token")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency
):
    user = (
        db.query(models.Users)
        .filter(models.Users.username == form_data.username)
        .first()
    )

    if not user:
        print("not user")
        raise UNAUTHORIZED

    if user:
        if not pwd_context.verify(form_data.password, user.hashed_pw):
            print("pw not matched")

            raise UNAUTHORIZED

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
        },
        expires_delta=access_token_expires,
    )
    user_dict = user_to_dict(user)

    return {"access_token": access_token, "token_type": "bearer", "user": user_dict}


@app.get("/users/me")
async def read_current_user(curr_user: UserBase = Depends(get_current_user)):
    return curr_user


@app.patch("/users/me")
async def edit_current_user(
    creds: ZendeskCredsBase,
    db: db_dependency,
    curr_user: UserBase = Depends(get_current_user),
):
    print(curr_user)
    if creds.apikey != None:
        user = db.query(models.Users).filter(models.Users.id == curr_user["id"]).first()
        (
            db.query(models.Users)
            .filter(models.Users.id == curr_user["id"])
            .update({"apikey": creds.apikey})
        )
    if creds.subdomain != None:
        user = db.query(models.Users).filter(models.Users.id == curr_user["id"]).first()
        (
            db.query(models.Users)
            .filter(models.Users.id == curr_user["id"])
            .update({"subdomain": creds.subdomain})
        )

    db.commit()
    db.refresh(user)
    print(user)
    print(type(user))
    userdict = user.__dict__.copy()
    del userdict["hashed_pw"]
    return {"status": status.HTTP_200_OK, "data": userdict}


# CHAT ROUTES


@app.post("/chats")
async def create_chat(
    db: db_dependency, curr_user: UserBase = Depends(get_current_user)
):
    db_chat = models.Chats(uid=curr_user["id"])
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat


@app.get("/chats")
async def create_chat(
    db: db_dependency, curr_user: UserBase = Depends(get_current_user)
):
    response_array = []
    user_chats = (
        db.query(models.Chats)
        .filter(models.Chats.uid == curr_user["id"])
        .order_by(models.Chats.created_at.desc())
        .all()
    )

    for chat in user_chats:
        messages = (
            db.query(models.Messages)
            .filter(models.Messages.cid == chat.id)
            .order_by(models.Messages.created_at)
            .all()
        )
        full_chat = {**chat.__dict__.copy(), "messages": messages}
        response_array.append(full_chat)
    return response_array


@app.get("/chats/{id}")
async def create_chat(
    id, db: db_dependency, curr_user: UserBase = Depends(get_current_user)
):
    user_chat = (
        db.query(models.Chats)
        .filter(models.Chats.uid == curr_user["id"])
        .filter(models.Chats.id == id)
        .first()
    )

    if not user_chat:
        raise NOT_FOUND

    messages = (
        db.query(models.Messages)
        .filter(models.Messages.cid == id)
        .order_by(models.Messages.created_at)
        .all()
    )
    full_chat = {**user_chat.__dict__.copy(), "messages": messages}

    return full_chat


@app.post("/chats/{id}/messages")
async def create_message(
    id,
    message: MessageBase,
    db: db_dependency,
    curr_user: UserBase = Depends(get_current_user),
):
    user_chat = (
        db.query(models.Chats)
        .filter(models.Chats.uid == curr_user["id"])
        .filter(models.Chats.id == id)
        .first()
    )

    if not user_chat:
        raise NOT_FOUND

    if not user_chat.chatname:
        summarymsg = f"Summarize this into a heading: {message.message}"
        summarymsg = str(summarymsg)
        res = generate_gpt(summarymsg)
        db.query(models.Chats).filter(models.Chats.uid == curr_user["id"]).filter(
            models.Chats.id == id
        ).update({"chatname": res})
        db.refresh(user_chat)

    history = (
        db.query(models.Messages)
        .filter(models.Messages.cid == id)
        .order_by(models.Messages.created_at)
        .all()
    )

    hist_array = [{"role": x.role, "message": x.message_text} for x in history]

    user_msg = models.Messages(cid=id, message_text=message.message, role=message.role)
    db.add(user_msg)
    ticketData = json.dumps(
        get_all_tickets(token=curr_user["apikey"], subdomain=curr_user["subdomain"])
    )

    if not ticketData:
        raise BAD_REQUEST

    prompt = f"""
    {message.message}
    {ticketData}
    """
    gptres = generate_gpt(prompt, history=hist_array)

    if not gptres:
        raise BAD_REQUEST

    assistant_msg = models.Messages(cid=id, message_text=gptres, role="assistant")
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return {"response": assistant_msg, "tickets": ticketData}


# ZENDAI LOGICS


@app.get("/gpt")
async def get_gpt_response():
    res = generate_gpt(
        "Hi. You are my assitant. give response in json only, with response in an attribute}"
    )
    return json.loads(res)


@app.get("/zenpy")
async def get_all_zenpy_tickets():
    res = get_all_tickets()
    return res


@app.post("/zengpt")
async def get_zengpt_response(
    question: GPTQuestionBase, curr_user: UserBase = Depends(get_current_user)
):
    user = curr_user
    if user["apikey"] is None or user["subdomain"] is None:
        raise CREDENTIALS_NEEDED
    ticketData = json.dumps(
        get_all_tickets(token=user["apikey"], subdomain=user["subdomain"])
    )
    ticketreqs = get_ticket_requirement(question.question_text)
    prompt = f"""
    {question.question_text}
    {ticketData}
    """
    gptres = generate_gpt(prompt)

    return {"res": gptres, "reqs": json.loads(ticketreqs)}
