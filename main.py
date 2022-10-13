import os
from datetime import datetime

import zpp_serpent
from fastapi import Depends, FastAPI
from crypto.ecc import scalar_mult
from crypto.ecdh import make_keypair
from src.db import User, create_db_and_tables, get_async_session
from src.schemas import UserCreate, UserRead, UserUpdate, Note, Key
from src.service import NoteService, UserService
from src.settings import KEY_EXPIRATION_TIME
from src.users import auth_backend, current_active_user, fastapi_users

app = FastAPI()

app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)


@app.get("/")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}


@app.get("/get_public_key")
async def exchange_public_keys(alice_public_key: Key, user: User = Depends(current_active_user),
                               session=Depends(get_async_session)):
    await UserService.save_public_key(session, user.id, alice_public_key)
    return {"public_key": os.getenv("public_key")}


@app.post("/create_note")
async def create_note(note: Note, user: User = Depends(current_active_user), session=Depends(get_async_session)):
    if (datetime.now() - user.pk_updated_at).seconds > KEY_EXPIRATION_TIME:
        return {"message": "handshake required"}
    note_name, note_message = note.name, note.message
    try:
        note.name, note.message = await NoteService.decrypt_note(user, note)
        await NoteService.create_note(session, user.id, note)
        note.name, note.message = note_name, note_message
    except BaseException as e:
        print(e)
        return {"message": "ECDH error"}
    return {"message": note}


@app.get("/get_notes")
async def get_notes(user: User = Depends(current_active_user), session=Depends(get_async_session)):
    if (datetime.now() - user.pk_updated_at).seconds > KEY_EXPIRATION_TIME:
        return {"message": "handshake required"}
    notes = await NoteService.get_user_notes(session, user.id)
    shared_secret = scalar_mult(int(os.getenv('private_key')), eval(user.public_key))
    password = shared_secret[0].to_bytes(32, 'big')
    try:
        for note in notes:
            note.name = str(zpp_serpent.encrypt_CFB(note.name.encode(), password))
            note.message = str(zpp_serpent.encrypt_CFB(note.message.encode(), password))
    except BaseException:
        return {"message": "ECDH error"}
    return {"message": notes}


@app.post("/edit_note")
async def edit_note(note: Note, user: User = Depends(current_active_user),
                    session=Depends(get_async_session)):
    if (datetime.now() - user.pk_updated_at).seconds > KEY_EXPIRATION_TIME:
        return {"message": "handshake required"}
    try:
        note_name, note_message = note.name, note.message
        note.name, note.message = await NoteService.decrypt_note(user, note)
        await NoteService.update_note(session, note.name, note.message, user.id)
        note.name, note.message = note_name, note_message
    except BaseException:
        return {"message": "ECDH error"}
    return {"message": note}


@app.delete("/delete_note")
async def delete_note(note: Note, user: User = Depends(current_active_user), session=Depends(get_async_session)):
    if (datetime.now() - user.pk_updated_at).seconds > KEY_EXPIRATION_TIME:
        return {"message": "handshake required"}
    try:
        note.name, note.message = await NoteService.decrypt_note(user, note)
        deleted_note = await NoteService.delete_note(session, user.id, note)
    except BaseException:
        return {"message": "ECDH error"}
    return {"message": deleted_note}


@app.on_event("startup")
async def on_startup():
    if 'private_key' not in os.environ:
        bob_private_key, bob_public_key = make_keypair()
        os.environ['private_key'] = str(bob_private_key)
        os.environ['public_key'] = str(bob_public_key)
        print('keys were created')

    await create_db_and_tables()
