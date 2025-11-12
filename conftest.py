from __future__ import annotations

import functools
import os
from typing import Callable

import pytest

from tortoise.contrib.test import finalizer, initializer


def _switch_gtid_mode() -> Callable[[], None] | None:
    # SET gtid_mode to be OFF before testings
    # And SET it ON after test before finalizer
    from tortoise.contrib.test import _CONNECTIONS, _LOOP

    conn = _CONNECTIONS.get("models")
    assert conn is not None
    run_coro = _LOOP.run_until_complete

    async def get_var_value(statement: str) -> str:
        result = await conn.execute_query_dict(statement)
        return result[0]["Value"]

    async def is_enforce_gtid() -> bool:
        statement = "SHOW VARIABLES LIKE 'enforce_gtid_consistency';"
        return (await get_var_value(statement)) == "ON"

    async def is_gtid_mode_on() -> bool:
        statement = "SHOW VARIABLES LIKE 'gtid_mode';"
        return (await get_var_value(statement)) == "ON"

    async def set_enforce_gtid_off() -> None:
        statement = "SET GLOBAL enforce_gtid_consistency = OFF;"
        if await is_gtid_mode_on():
            off_mode = """
            SET GLOBAL gtid_mode = ON_PERMISSIVE;
            SET GLOBAL gtid_mode = OFF_PERMISSIVE;
            SET GLOBAL gtid_mode = OFF;
            """
            statement = off_mode + statement
        await conn.execute_script(statement)

    async def set_enforce_gtid_on() -> None:
        statement = "SET GLOBAL enforce_gtid_consistency = ON;"
        if not (await is_gtid_mode_on()):
            statement += """
            SET GLOBAL gtid_mode = OFF_PERMISSIVE;
            SET GLOBAL gtid_mode = ON_PERMISSIVE;
            SET GLOBAL gtid_mode = ON;
            """
        await conn.execute_script(statement)

    if run_coro(is_enforce_gtid()):
        run_coro(set_enforce_gtid_off())
        return functools.partial(run_coro, set_enforce_gtid_on())
    return None


@pytest.fixture(scope="session", autouse=True)
def initialize_tests():
    # Reduce the default timeout for psycopg because the tests become very slow otherwise
    try:
        from tortoise.backends.psycopg import PsycopgClient

        PsycopgClient.default_timeout = float(os.environ.get("TORTOISE_POSTGRES_TIMEOUT", "15"))
    except ImportError:
        pass

    db_url = os.getenv("TORTOISE_TEST_DB", "sqlite://:memory:")
    initializer(["tests.testmodels"], db_url=db_url)
    rollback_sets: Callable[[], None] | None = None
    if db_url.startswith("mysql") and "storage_engine=MYISAM" in db_url:
        # Fixes "tortoise.exceptions.OperationalError: (1785, 'Statement violates GTID consistency: ...')" for `make test_mysql_myisam`
        rollback_sets = _switch_gtid_mode()
    try:
        yield
    finally:
        if rollback_sets is not None:
            rollback_sets()
        finalizer()
