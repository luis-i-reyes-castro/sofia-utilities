from __future__ import annotations

import re
from collections import defaultdict
from contextlib import (
    asynccontextmanager,
    contextmanager,
)
from functools import lru_cache
from pathlib import Path
from psycopg import (
    AsyncConnection,
    AsyncCursor,
    Connection,
    Cursor,
)
from psycopg.rows import (
    DictRow,
    dict_row,
)
from psycopg.types.json import Jsonb
from psycopg_pool import (
    AsyncConnectionPool,
    ConnectionPool,
)
from typing import (
    Any,
    AsyncIterator,
    Iterator,
)


# -----------------------------------------------------------------------------------------
# TYPES AND GLOBAL VARIABLES

type Sync_DB_Connection = Connection[DictRow]
""" Sync Database Connection """
type Sync_DB_Cursor     = Cursor[DictRow]
""" Sync Database Cursor """

type DB_Connection = AsyncConnection[DictRow]
""" Async Database Connection """
type DB_Cursor     = AsyncCursor[DictRow]
""" Async Database Cursor """

sync_db_connection_pool : ConnectionPool[Sync_DB_Connection] | None = None
""" Global Sync Database Connection Pool """

db_connection_pool : AsyncConnectionPool[DB_Connection] | None = None
""" Global Async Database Connection Pool """


# -----------------------------------------------------------------------------------------
# POOLED SYNC DATABASE CONNECTION

def open_sync_database_connection_pool(
    database_url : str,
    min_size     : int   = 1,
    max_size     : int   = 5,
    timeout      : float = 30,
) -> None :
    """
    Open the sync database connection pool. \\
    Args:
        database_url : Database connection URL
        min_size     : Database pool minimum size
        max_size     : Database pool maximum size
        timeout      : Database pool timeout
    """
    global sync_db_connection_pool

    if sync_db_connection_pool is None :
        pool = ConnectionPool(
            conninfo = database_url,
            min_size = min_size,
            max_size = max_size,
            timeout  = timeout,
            kwargs   = { "row_factory" : dict_row },
            open     = False,
        )
        pool.open()
        sync_db_connection_pool = pool

    return


def close_sync_database_connection_pool() -> None :
    """
    Close the sync database connection pool.
    """
    global sync_db_connection_pool

    if sync_db_connection_pool is not None :
        sync_db_connection_pool.close()
        sync_db_connection_pool = None

    return


@contextmanager
def sync_pooled_conection(
    database_url : str | None = None,
    min_size     : int        = 1,
    max_size     : int        = 5,
    timeout      : float      = 30,
) -> Iterator[Sync_DB_Connection] :
    """
    Open the sync database connection pool if needed and yield a connection. \\
    Args:
        database_url : Database connection URL. Required when pool is not open.
        min_size     : Database pool minimum size
        max_size     : Database pool maximum size
        timeout      : Database pool timeout
    """
    if sync_db_connection_pool is None :
        if database_url is None :
            raise RuntimeError(
                "Database pool is not initialized and database_url is unset"
            )
        open_sync_database_connection_pool(
            database_url = database_url,
            min_size     = min_size,
            max_size     = max_size,
            timeout      = timeout,
        )

    pool = sync_db_connection_pool
    if pool is None :
        raise RuntimeError("Database pool is not initialized")

    with pool.connection() as db_connection :
        yield db_connection


# -----------------------------------------------------------------------------------------
# POOLED DATABASE CONNECTION

async def open_async_database_connection_pool(
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


async def close_async_database_connection_pool() -> None :
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
        await open_async_database_connection_pool(
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
