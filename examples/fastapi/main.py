# pylint: disable=E0611,E0401
from contextlib import asynccontextmanager

from fastapi import FastAPI
from views import app as users_router

from tortoise.contrib.fastapi import RegisterTortoise


@asynccontextmanager
async def lifespan(app):
    async with RegisterTortoise(
        app,
        db_url="sqlite://:memory:",
        modules={"models": ["models"]},
        generate_schemas=True,
        add_exception_handlers=True,
    ):
        yield


app = FastAPI(title="Tortoise ORM FastAPI example", lifespan=lifespan)
app.include_router(users_router)
