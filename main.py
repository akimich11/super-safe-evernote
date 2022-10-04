from fastapi import Depends, FastAPI
from src.db import User, create_db_and_tables, get_async_session
from src.schemas import UserCreate, UserRead, UserUpdate, Note
from src.service import NoteService
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


@app.post("/create_note")
async def create_note(note: Note, user: User = Depends(current_active_user), session=Depends(get_async_session)):
    created_note = await NoteService.create_note(session, user.id, note)
    return {"message": created_note}


@app.get("/get_notes")
async def get_notes(user: User = Depends(current_active_user), session=Depends(get_async_session)):
    notes = await NoteService.get_user_notes(session, user.id)
    return {"message": notes}


@app.post("/edit_note/{note_id}")
async def edit_note(note_id: int, note: Note, user: User = Depends(current_active_user),
                    session=Depends(get_async_session)):
    updated_note = await NoteService.update_note(session, note_id, note, user.id)
    return {"message": updated_note}


@app.delete("/delete_note/{note_id}")
async def create_note(note_id: int, user: User = Depends(current_active_user), session=Depends(get_async_session)):
    deleted_note = await NoteService.delete_note(session, user.id, note_id)
    return {"message": deleted_note}


@app.on_event("startup")
async def on_startup():
    # Not needed if you set up a migration system like Alembic
    await create_db_and_tables()
