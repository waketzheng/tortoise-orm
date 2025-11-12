from __future__ import annotations

import contextlib
import functools
import os
from typing import Callable

import pytest

from tortoise.contrib.test import finalizer, initializer


def _switch_gtid_mode() -> Callable[[], None] | None:
    # SET gtid_mode to be OFF before testings
    # And SET it ON after test before finalizer
    from tortoise.contrib.test import _CONNECTIONS, _LOOP
    from tortoise.exceptions import OperationalError

    conn = _CONNECTIONS.get("models")
    assert conn is not None
    run_coro = _LOOP.run_until_complete

    async def get_var_value(statement: str) -> str:
        result = await conn.execute_query_dict(statement)
        return result[0]["Value"]

    async def is_enforce_gtid() -> bool:
        statement = "SHOW VARIABLES LIKE 'enforce_gtid_consistency';"
        return (await get_var_value(statement)).upper() == "ON"

    async def get_gtid_mode_status() -> str:
        statement = "SHOW VARIABLES LIKE 'gtid_mode';"
        return await get_var_value(statement)

    async def set_enforce_gtid_off(mode_on: bool, gtid_mode: str) -> None:
        statement = "SET GLOBAL enforce_gtid_consistency = OFF;"
        if mode_on:
            if gtid_mode == "ON":
                await conn.execute_script("SET GLOBAL gtid_mode = ON_PERMISSIVE;")
            await conn.execute_script("SET GLOBAL gtid_mode = OFF_PERMISSIVE;")
        await conn.execute_script(statement)

    async def set_enforce_gtid_on(mode_on: bool, origin_gtid_mode: str) -> None:
        statement = "SET GLOBAL enforce_gtid_consistency = ON;"
        await conn.execute_script(statement)
        if mode_on:
            current_status = (await get_gtid_mode_status()).upper()
            if current_status == origin_gtid_mode.upper():
                return
            with contextlib.suppress(OperationalError):
                if current_status == "OFF":
                    await conn.execute_script("SET GLOBAL gtid_mode = OFF_PERMISSIVE;")
                await conn.execute_script("SET GLOBAL gtid_mode = ON_PERMISSIVE;")
                if origin_gtid_mode.upper() == "ON":
                    await conn.execute_script("SET GLOBAL gtid_mode = ON;")

    if run_coro(is_enforce_gtid()):
        origin_gtid_mode = run_coro(get_gtid_mode_status())
        gtid_mode = origin_gtid_mode.upper()
        mode_on = gtid_mode.startswith("ON")
        run_coro(set_enforce_gtid_off(mode_on, gtid_mode))
        if mode_on and not os.getenv("TORTOISE_GTID_KEEP_OFF"):
            return functools.partial(run_coro, set_enforce_gtid_on(mode_on, origin_gtid_mode))
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
