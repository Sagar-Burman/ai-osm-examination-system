"""Add the documented EVALUATED_OK value to the existing sheets.status enum."""

import re

from sqlalchemy import inspect, text

from app.db.database import engine


def main() -> None:
    with engine.begin() as conn:
        inspector = inspect(conn)
        columns = inspector.get_columns("sheets")
        status_col = next((c for c in columns if c["name"] == "status"), None)

        if status_col is None:
            raise RuntimeError("sheets.status column not found")

        enum_type_name = getattr(status_col["type"], "name", None)

        if enum_type_name and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", enum_type_name):
            conn.execute(
                text(
                    f"ALTER TYPE {enum_type_name} "
                    "ADD VALUE IF NOT EXISTS 'EVALUATED_OK'"
                )
            )
            print("Stage 25 submit transition: EVALUATED_OK verified")
        else:
            print("Stage 25 submit transition: status is not a native enum; no DB enum change needed")


if __name__ == "__main__":
    main()
