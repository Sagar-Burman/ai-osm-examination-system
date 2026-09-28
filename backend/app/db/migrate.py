from sqlalchemy import inspect, text

from app.db.database import engine


def migrate():
    inspector = inspect(engine)

    with engine.begin() as conn:

        # -------------------------
        # EXAMS TABLE
        # -------------------------
        exam_columns = {
            column["name"]
            for column in inspector.get_columns("exams")
        }

        if "expected_pages" not in exam_columns:
            conn.execute(
                text(
                    "ALTER TABLE exams "
                    "ADD COLUMN expected_pages INTEGER"
                )
            )

        if "mark_step" not in exam_columns:
            conn.execute(
                text(
                    "ALTER TABLE exams "
                    "ADD COLUMN mark_step REAL NOT NULL DEFAULT 0.5"
                )
            )

        if "is_locked" not in exam_columns:
            conn.execute(
                text(
                    "ALTER TABLE exams "
                    "ADD COLUMN is_locked BOOLEAN NOT NULL DEFAULT FALSE"
                )
            )

        if "created_by" not in exam_columns:
            conn.execute(
                text(
                    "ALTER TABLE exams "
                    "ADD COLUMN created_by INTEGER"
                )
            )

            conn.execute(
                text(
                    "UPDATE exams "
                    "SET created_by = 1 "
                    "WHERE created_by IS NULL"
                )
            )

            conn.execute(
                text(
                    "ALTER TABLE exams "
                    "ALTER COLUMN created_by SET NOT NULL"
                )
            )

        if "created_at" not in exam_columns:
            conn.execute(
                text(
                    "ALTER TABLE exams "
                    "ADD COLUMN created_at TIMESTAMP"
                )
            )

            conn.execute(
                text(
                    "UPDATE exams "
                    "SET created_at = CURRENT_TIMESTAMP "
                    "WHERE created_at IS NULL"
                )
            )

            conn.execute(
                text(
                    "ALTER TABLE exams "
                    "ALTER COLUMN created_at SET NOT NULL"
                )
            )

        # Add exam -> users foreign key if missing
        exam_fks = inspector.get_foreign_keys("exams")

        has_created_by_fk = any(
            fk.get("constrained_columns") == ["created_by"]
            and fk.get("referred_table") == "users"
            for fk in exam_fks
        )

        if not has_created_by_fk:
            conn.execute(
                text(
                    "ALTER TABLE exams "
                    "ADD CONSTRAINT fk_exams_created_by_users "
                    "FOREIGN KEY (created_by) REFERENCES users(id)"
                )
            )

        # -------------------------
        # QUESTIONS TABLE
        # -------------------------
        question_columns = {
            column["name"]
            for column in inspector.get_columns("questions")
        }

        if "rubric" not in question_columns and "rubric_items" in question_columns:
            conn.execute(
                text(
                    "ALTER TABLE questions "
                    "RENAME COLUMN rubric_items TO rubric"
                )
            )

        if "is_optional" not in question_columns:
            conn.execute(
                text(
                    "ALTER TABLE questions "
                    "ADD COLUMN is_optional BOOLEAN NOT NULL DEFAULT FALSE"
                )
            )

        conn.execute(
            text(
                "ALTER TABLE questions "
                "ALTER COLUMN question_number TYPE VARCHAR(20) "
                "USING question_number::text"
            )
        )

        # -------------------------
        # UNIQUE QUESTION NUMBER
        # -------------------------
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "uq_questions_exam_number "
                "ON questions (exam_id, question_number)"
            )
        )

    print("Database migration completed successfully")


if __name__ == "__main__":
    migrate()