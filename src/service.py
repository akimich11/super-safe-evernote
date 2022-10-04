from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src import schemas, models


class NoteService:
    @staticmethod
    async def create_note(session: AsyncSession, user_id: UUID, note: schemas.Note):
        user = await session.get(models.User, {'id': user_id})
        note = models.Note(
            user_id=user.id,
            name=note.name,
            message=note.message
        )
        session.add(note)
        await session.commit()
        await session.refresh(note)
        return note

    @staticmethod
    async def get_user_notes(session: AsyncSession, user_id: UUID):
        stmt = select(models.User).where(models.User.id == user_id).options(selectinload(models.User.notes))
        result = await session.execute(stmt)
        user = result.scalars().one()
        return user.notes

    @staticmethod
    async def update_note(session: AsyncSession, note_id: int, note: schemas.Note, user_id: UUID):
        note_from_db = await session.get(models.Note, {'id': note_id})
        if note_from_db.user_id != user_id:
            return "This is not your note, you can't edit it"
        note_from_db.name = note.name
        note_from_db.message = note.message

        await session.commit()
        await session.refresh(note_from_db)
        return note_from_db

    @staticmethod
    async def delete_note(session, user_id, note_id):
        note_from_db = await session.get(models.Note, {'id': note_id})
        if note_from_db.user_id != user_id:
            return "This is not your note, you can't delete it"
        await session.delete(note_from_db)
        await session.commit()
