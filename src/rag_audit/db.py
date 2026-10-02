from pathlib import Path

import psycopg

from rag_audit.settings import Settings


class DatabaseCheckError(RuntimeError):
    pass


def execute_database_command(
    settings: Settings, *, init_sql: str | None = None
) -> bool:
    if settings.database_url is None or not settings.database_url.get_secret_value():
        raise DatabaseCheckError("DATABASE_URL is required for database operations.")
    try:
        with psycopg.connect(
            settings.database_url.get_secret_value(),
            connect_timeout=settings.database_connect_timeout,
        ) as connection:
            with connection.cursor() as cursor:
                if init_sql is not None:
                    cursor.execute(init_sql)
                cursor.execute(
                    "SELECT EXISTS (SELECT 1 FROM pg_extension "
                    "WHERE extname = 'vector')"
                )
                result = cursor.fetchone()
                return result is not None and bool(result[0])
    except psycopg.Error:
        raise DatabaseCheckError("Database connection or operation failed.") from None


def check_vector_extension(settings: Settings) -> bool:
    return execute_database_command(settings)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Initialise the synthetic demo database"
    )
    parser.add_argument("--init-sql", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        available = execute_database_command(
            Settings(), init_sql=arguments.init_sql.read_text(encoding="utf-8")
        )
        if not available:
            raise DatabaseCheckError("The vector extension is unavailable.")
    except (DatabaseCheckError, OSError, ValueError):
        print(
            "Database initialisation failed; "
            "check configuration and database readiness."
        )
        return 1
    print("Database initialised; vector extension is available.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
