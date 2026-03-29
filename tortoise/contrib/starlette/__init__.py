from __future__ import annotations

from collections.abc import Iterable
from contextlib import asynccontextmanager
from types import ModuleType
from typing import TYPE_CHECKING

from starlette.routing import _DefaultLifespan as StarletteDefaultLifespan

from tortoise import Tortoise
from tortoise.connection import get_connections
from tortoise.log import logger

if TYPE_CHECKING:
    from starlette.applications import Starlette  # pylint: disable=E0401


def register_tortoise(
    app: Starlette,
    config: dict | None = None,
    config_file: str | None = None,
    db_url: str | None = None,
    modules: dict[str, Iterable[str | ModuleType]] | None = None,
    generate_schemas: bool = False,
) -> None:
    """
    Registers ``startup`` and ``shutdown`` events to set-up and tear-down Tortoise-ORM
    inside a Starlette application.

    You can configure using only one of ``config``, ``config_file``
    and ``(db_url, modules)``.

    Parameters
    ----------
    app:
        Starlette app.
    config:
        Dict containing config:

        Example
        -------

        .. code-block:: python3

            {
                'connections': {
                    # Dict format for connection
                    'default': {
                        'engine': 'tortoise.backends.asyncpg',
                        'credentials': {
                            'host': 'localhost',
                            'port': '5432',
                            'user': 'tortoise',
                            'password': 'qwerty123',
                            'database': 'test',
                        }
                    },
                    # Using a DB_URL string
                    'default': 'postgres://postgres:qwerty123@localhost:5432/events'
                },
                'apps': {
                    'models': {
                        'models': ['__main__'],
                        # If no default_connection specified, defaults to 'default'
                        'default_connection': 'default',
                    }
                }
            }

    config_file:
        Path to .json or .yml (if PyYAML installed) file containing config with
        same format as above.
    db_url:
        Use a DB_URL string. See :ref:`db_url`
    modules:
        Dictionary of ``key``: [``list_of_modules``] that defined "apps" and modules that
        should be discovered for models.
    generate_schemas:
        True to generate schema immediately. Only useful for dev environments
        or SQLite ``:memory:`` databases

    Raises
    ------
    ConfigurationError
        For any configuration error
    """

    async def init_orm() -> None:  # pylint: disable=W0612
        await Tortoise.init(config=config, config_file=config_file, db_url=db_url, modules=modules)
        logger.info("Tortoise-ORM started, %s, %s", get_connections()._get_storage(), Tortoise.apps)
        if generate_schemas:
            logger.info("Tortoise-ORM generating schema")
            await Tortoise.generate_schemas()

    async def close_orm() -> None:  # pylint: disable=W0612
        await Tortoise.close_connections()
        logger.info("Tortoise-ORM shutdown")

    @asynccontextmanager
    async def orm_lifespan(app_instance: Starlette):
        await init_orm()
        try:
            yield
        finally:
            await close_orm()

    original_lifespan = app.router.lifespan_context
    if isinstance(original_lifespan, StarletteDefaultLifespan):
        app.router.lifespan_context = orm_lifespan
    else:

        @asynccontextmanager
        async def merged_lifespan(app_instance: Starlette):
            async with orm_lifespan(app_instance):
                async with original_lifespan(app_instance) as maybe_state:
                    if maybe_state is None:
                        yield
                    else:
                        yield {**(maybe_state or {})}

        app.router.lifespan_context = merged_lifespan
