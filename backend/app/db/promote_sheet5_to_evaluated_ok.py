"""Promote an already-submitted, fully evaluated sheet to EVALUATED_OK.

This is a one-time data migration for the existing demo sheet after the
Stage 25 lifecycle fix was added. It only promotes sheet 5 when it is still
SUBMITTED and has no OPEN flags.
"""

from sqlalchemy import text

from app.db.database import engine


def main() -> None:
    sheet_id = 5
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT status FROM sheets WHERE id = :sheet_id"),
            {"sheet_id": sheet_id},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Sheet {sheet_id} not found")

        status = row[0]
        if status == "EVALUATED_OK":
            print(f"Sheet {sheet_id}: already EVALUATED_OK")
            return

        if status != "SUBMITTED":
            raise RuntimeError(
                f"Sheet {sheet_id} is {status}; expected SUBMITTED"
            )

        open_flag = conn.execute(
            text(
                "SELECT 1 FROM flags "
                "WHERE sheet_id = :sheet_id AND status = 'OPEN' "
                "LIMIT 1"
            ),
            {"sheet_id": sheet_id},
        ).fetchone()
        if open_flag is not None:
            raise RuntimeError(
                f"Sheet {sheet_id} has OPEN flags; not promoted"
            )

        conn.execute(
            text(
                "UPDATE sheets SET status = 'EVALUATED_OK' "
                "WHERE id = :sheet_id AND status = 'SUBMITTED'"
            ),
            {"sheet_id": sheet_id},
        )

        print(f"Sheet {sheet_id}: SUBMITTED -> EVALUATED_OK")


if __name__ == "__main__":
    main()
