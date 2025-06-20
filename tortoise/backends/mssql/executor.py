from __future__ import annotations

import re
from typing import Any

from pypika_tortoise.enums import SqlTypes
from pypika_tortoise.functions import Cast, Upper
from pypika_tortoise.terms import (
    Criterion,
    Term,
)

from tortoise.backends.odbc.executor import ODBCExecutor
from tortoise.exceptions import UnSupportedError
from tortoise.filters import Like


def escape_backslash_except_wildcards(val: str) -> str:
    # Replace \ with \\ if the backslash is not followed by % or _
    return re.sub(r"\\(?![%_])", r"\\", val)


def like(field: Term, value: str) -> Criterion:
    return Like(
        Cast(field, SqlTypes.VARCHAR),
        field.wrap_constant(value),
    )


def ilike(field: Term, value: str) -> Criterion:
    return Like(
        Upper(Cast(field, SqlTypes.VARCHAR)),
        field.wrap_constant(Upper(value)),
    )


class MSSQLExecutor(ODBCExecutor):
    FILTER_FUNC_OVERRIDE = {like: like, ilike: ilike}

    async def execute_explain(self, sql: str) -> Any:
        raise UnSupportedError("MSSQL does not support explain")
