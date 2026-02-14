#!/usr/bin/env python3
"""Reset database for testing - CAUTION: DESTROYS ALL DATA"""
import asyncio

from sqlmodel import SQLModel

from app.core.database import async_engine
from app.models import models  # noqa: F401


async def reset():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    print("✅ Database reset complete")


if __name__ == "__main__":
    asyncio.run(reset())
