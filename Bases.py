from pydantic import BaseModel
from typing import Annotated, List


class ChoiceBase(BaseModel):
    choice_text: str
    is_correct: bool


class QuestionBase(BaseModel):
    question_text: str
    choices: List[ChoiceBase]


class UserBase(BaseModel):
    username: str
    email: str
    hashed_pw: str


class UserCreationBase(BaseModel):
    username: str
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str or None = None


class ZendeskCredsBase(BaseModel):
    subdomain: str or None = None
    apikey: str or None = None


class GPTQuestionBase(BaseModel):
    question_text: str


class MessageBase(BaseModel):
    role: str
    message: str
