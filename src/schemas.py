import uuid
from fastapi_users import schemas
from pydantic import BaseModel, constr


class Note(BaseModel):
    name: constr(min_length=1, max_length=256)
    message: constr(min_length=1)


class Key(BaseModel):
    public_key: str


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass
