from __future__ import annotations

import re
from collections import defaultdict
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from psycopg import (
    AsyncConnection,
    AsyncCursor,
)
from psycopg.rows import (
    DictRow,
    dict_row,
)
from psycopg_pool import AsyncConnectionPool
from typing import (
    Any,
    AsyncIterator,
)


# -----------------------------------------------------------------------------------------
# TYPES AND GLOBAL VARIABLES

type DB_Connection = AsyncConnection[DictRow]
""" Async Database Connection """
type DB_Cursor     = AsyncCursor[DictRow]
""" Async Database Cursor """

db_connection_pool : AsyncConnectionPool[DB_Connection] | None = None
""" Global Database Connection Pool """


# -----------------------------------------------------------------------------------------
# POOLED DATABASE CONNECTION

async def open_database_connection_pool(
    database_url : str,
    min_size     : int   = 1,
    max_size     : int   = 5,
    timeout      : float = 30,
) -> None :
    """
    Open the database connection pool. \\
    Args:
        database_url : Database connection URL
        min_size     : Database pool minimum size
        max_size     : Database pool maximum size
        timeout      : Database pool timeout
    """
    global db_connection_pool
    
    if db_connection_pool is None :
        pool = AsyncConnectionPool(
            conninfo = database_url,
            min_size = min_size,
            max_size = max_size,
            timeout  = timeout,
            kwargs   = { "row_factory" : dict_row },
            open     = False,
        )
        await pool.open()
        db_connection_pool = pool
    
    return


async def close_database_connection_pool() -> None :
    """
    Close the database connection pool.
    """
    global db_connection_pool
    
    if db_connection_pool is not None :
        await db_connection_pool.close()
        db_connection_pool = None
    
    return


@asynccontextmanager
async def async_pooled_connection(
    database_url : str | None = None,
    min_size     : int        = 1,
    max_size     : int        = 5,
    timeout      : float      = 30,
) -> AsyncIterator[DB_Connection] :
    """
    Open the database connection pool if needed and yield an async connection. \\
    Args:
        database_url : Database connection URL. Required when pool is not open.
        min_size     : Database pool minimum size
        max_size     : Database pool maximum size
        timeout      : Database pool timeout
    """
    if db_connection_pool is None :
        if database_url is None :
            raise RuntimeError("Database pool is not initialized and database_url is unset")
        await open_database_connection_pool(
            database_url = database_url,
            min_size     = min_size,
            max_size     = max_size,
            timeout      = timeout,
        )
    
    pool = db_connection_pool
    if pool is None :
        raise RuntimeError("Database pool is not initialized")
    
    async with pool.connection() as db_connection :
        yield db_connection


# -----------------------------------------------------------------------------------------
# WRAPPERS

@lru_cache( maxsize = 32)
def load_sql_script( filepath : str | Path) -> str :
    """
    Load SQL script and replace `@named_parameter` with `%(named_parameter)s`. \\
    Raises `FileNotFoundError` if file is not found. \n
    Caveats:
    * IGNORES single-quoted emails, e.g., `'no@mail.com'`.
    * DOES NOT IGNORE strings when not adjacent to quotes, e.g. `'hello @name world'`.
    """
    return re.sub(
        pattern = r"(?<!['\w.%+-])@([A-Za-z_]\w*)(?!['\w.])",
        repl    = r"%(\1)s",
        string  = Path(filepath).read_text( encoding = "utf-8"),
    )


def wrap_params( params_dict : dict[ str, Any]) -> defaultdict[ str, Any] :
    """
    Wrap a `defaultdict` with `default_factory = lambda : None`
    around a query parameters dictionary.
    """
    return defaultdict( lambda : None, params_dict)
