from typing import TYPE_CHECKING, Any, Awaitable, Iterable, Optional

import anyio

from tortoise.log import logger

if TYPE_CHECKING:  # pragma: nocoverage
    from tortoise.backends.base.client import BaseDBAsyncClient


def get_schema_sql(client: "BaseDBAsyncClient", safe: bool) -> str:
    """
    Generates the SQL schema for the given client.

    :param client: The DB client to generate Schema SQL for
    :param safe: When set to true, creates the table only when it does not already exist.
    """
    generator = client.schema_generator(client)
    return generator.get_create_schema_sql(safe)


async def generate_schema_for_client(client: "BaseDBAsyncClient", safe: bool) -> None:
    """
    Generates and applies the SQL schema directly to the given client.

    :param client: The DB client to generate Schema SQL for
    :param safe: When set to true, creates the table only when it does not already exist.
    """
    generator = client.schema_generator(client)
    schema = get_schema_sql(client, safe)
    logger.debug("Creating schema: %s", schema)
    if schema:  # pragma: nobranch
        await generator.generate_from_string(schema)


def chunk(instances: Iterable[Any], batch_size: Optional[int] = None) -> Iterable[Iterable[Any]]:
    """
    Generate iterable chunk by batch_size
    # noqa: DAR301
    """
    if not batch_size:
        yield instances
    else:
        instances = list(instances)
        for i in range(0, len(instances), batch_size):
            yield instances[i : i + batch_size]  # noqa:E203


async def gather(*coros: Awaitable) -> None:
    async def runner(c):
        await c

    async with anyio.create_task_group() as tg:
        for c in coros:
            tg.start_soon(runner, c)
