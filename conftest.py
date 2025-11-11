from __future__ import annotations

import functools
import os
from typing import Any, Callable

import pytest

from tortoise.contrib.test import finalizer, initializer


@pytest.fixture(scope="session", autouse=True)
def initialize_tests(request):
    # Reduce the default timeout for psycopg because the tests become very slow otherwise
    try:
        from tortoise.backends.psycopg import PsycopgClient

        PsycopgClient.default_timeout = float(os.environ.get("TORTOISE_POSTGRES_TIMEOUT", "15"))
    except ImportError:
        pass

    db_url = os.getenv("TORTOISE_TEST_DB", "sqlite://:memory:")
    initializer(["tests.testmodels"], db_url=db_url)
    rollback_vars: Callable[[], Any] | None = None
    if db_url.startswith("mysql") and "storage_engine=MYISAM" in db_url:
        # Fixes "tortoise.exceptions.OperationalError: (1785, 'Statement violates GTID consistency: ...')" for `make test_mysql_myisam`
        from tortoise.contrib.test import _CONNECTIONS, _LOOP

        conn = _CONNECTIONS.get("models")
        assert conn is not None
        run_async = _LOOP.run_until_complete

        def get_var_value(statement: str) -> str:
            result = run_async(conn.execute_query(statement))
            return result[1][0]["Value"]

        def is_enforce_gtid() -> bool:
            statement = "SHOW VARIABLES LIKE 'enforce_gtid_consistency';"
            return get_var_value(statement) == "ON"

        def is_gtid_mode_on() -> bool:
            statement = "SHOW VARIABLES LIKE 'gtid_mode';"
            return get_var_value(statement) == "ON"

        async def set_enforce_gtid_off(switch_mode: bool) -> None:
            statement = "SET GLOBAL enforce_gtid_consistency = OFF;"
            if switch_mode:
                off_mode = """
                SET GLOBAL gtid_mode = ON_PERMISSIVE;
                SET GLOBAL gtid_mode = OFF_PERMISSIVE;
                SET GLOBAL gtid_mode = OFF;
                """
                statement = off_mode + statement
            await conn.execute_script(statement)

        async def set_enforce_gtid_on(switch_mode: bool) -> None:
            statement = "SET GLOBAL enforce_gtid_consistency = ON;"
            if switch_mode:
                statement += """
                SET GLOBAL gtid_mode = OFF_PERMISSIVE;
                SET GLOBAL gtid_mode = ON_PERMISSIVE;
                SET GLOBAL gtid_mode = ON;
                """
            await conn.execute_script(statement)

        if is_enforce_gtid():
            mode_on = is_gtid_mode_on()
            run_async(set_enforce_gtid_off(mode_on))
            rollback_vars = functools.partial(run_async, set_enforce_gtid_on(mode_on))

    request.addfinalizer(finalizer)
    if rollback_vars is not None:
        request.addfinalizer(rollback_vars)
