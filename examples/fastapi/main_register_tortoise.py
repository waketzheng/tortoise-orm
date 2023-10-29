# pylint: disable=E0611,E0401
from fastapi import FastAPI
from views import app as users_router

from tortoise.contrib.fastapi import register_tortoise

app = FastAPI(title="Tortoise ORM FastAPI example")
register_tortoise(
    app,
    db_url="sqlite://:memory:",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)
app.include_router(users_router)
