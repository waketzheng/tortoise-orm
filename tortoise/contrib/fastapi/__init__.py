from __future__ import annotations

import asyncio
from contextlib import AbstractAsyncContextManager
from types import ModuleType
from typing import Dict, Generator, Iterable, Optional, Union

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse

from tortoise import Tortoise, connections
from tortoise.exceptions import DoesNotExist, IntegrityError
from tortoise.log import logger


class RegisterTortoise(AbstractAsyncContextManager):
    """Register Tortoise-ORM set-up and tear-down in lifespan.

    Usage:

    .. code-block:: python3

        def lifespan(app):
            async with RegisterTortoise(app, ...):
                yield

    Or:

    .. code-block:: python3

        def lifespan(app):
            orm = await RegisterTortoise(app, ...)
            yield
            await orm.close()

    You can configure using only one of ``config``, ``config_file``
    and ``(db_url, modules)``.

    Parameters
    ----------
    app:
        FastAPI app.
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
    add_exception_handlers:
        True to add some automatic exception handlers for ``DoesNotExist`` & ``IntegrityError``.
        This is not recommended for production systems as it may leak data.

    Raises
    ------
    ConfigurationError
        For any configuration error
    """

    def __init__(
        self,
        app: FastAPI,
        config: Optional[dict] = None,
        config_file: Optional[str] = None,
        db_url: Optional[str] = None,
        modules: Optional[Dict[str, Iterable[Union[str, ModuleType]]]] = None,
        generate_schemas: bool = False,
        add_exception_handlers: bool = False,
    ) -> None:
        self.app = app
        self.config = config
        self.config_file = config_file
        self.db_url = db_url
        self.modules = modules
        self.generate_schemas = generate_schemas
        self.add_exception_handlers = add_exception_handlers

    @staticmethod
    async def init_orm(config, config_file, db_url, modules, generate_schemas) -> None:
        await Tortoise.init(config=config, config_file=config_file, db_url=db_url, modules=modules)
        logger.info("Tortoise-ORM started, %s, %s", connections._get_storage(), Tortoise.apps)
        if generate_schemas:
            logger.info("Tortoise-ORM generating schema")
            await Tortoise.generate_schemas()

    @staticmethod
    async def close() -> None:
        await connections.close_all()
        logger.info("Tortoise-ORM shutdown")

    @staticmethod
    def register_exception_handlers(app) -> None:
        @app.exception_handler(DoesNotExist)  # type:ignore
        async def doesnotexist_exception_handler(request: Request, exc: DoesNotExist):
            return JSONResponse(status_code=404, content={"detail": str(exc)})

        @app.exception_handler(IntegrityError)  # type:ignore
        async def integrityerror_exception_handler(request: Request, exc: IntegrityError):
            return JSONResponse(
                status_code=422,
                content={"detail": [{"loc": [], "msg": str(exc), "type": "IntegrityError"}]},
            )

    async def init(self) -> None:
        await self.init_orm(
            self.config, self.config_file, self.db_url, self.modules, self.generate_schemas
        )

    def __await__(self) -> Generator[None, None, "RegisterTortoise"]:
        yield from asyncio.create_task(self.init())
        self.register_exception_handlers(self.app)
        return self

    async def __aenter__(self) -> "RegisterTortoise":
        await self.init()
        self.register_exception_handlers(self.app)
        return self

    async def __aexit__(self, *args, **kwargs) -> None:
        await self.close()


def register_tortoise(
    app: FastAPI,
    config: Optional[dict] = None,
    config_file: Optional[str] = None,
    db_url: Optional[str] = None,
    modules: Optional[Dict[str, Iterable[Union[str, ModuleType]]]] = None,
    generate_schemas: bool = False,
    add_exception_handlers: bool = False,
) -> None:
    """
    Leave it to compare with older version that is <= 0.20.0
    For newer version, use `RegiterTortoise` instead.
    """
    orm = RegisterTortoise(app, config, config_file, db_url, modules, generate_schemas)

    class Manager(AbstractAsyncContextManager):
        def __init__(self, app: FastAPI):
            pass

        def __await__(self) -> Generator[None, None, "Manager"]:
            yield from asyncio.create_task(orm.init())
            return self

        async def __aenter__(self) -> None:
            await orm.init()

        async def __aexit__(self, *args, **kwargs) -> None:
            await orm.close()

    if add_exception_handlers:
        orm.register_exception_handlers(app)

    app.router.lifespan_context = Manager
