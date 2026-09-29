from app.db.base import Base
from app.db.database import engine

# Import the existing model modules so SQLAlchemy knows all referenced
# tables before creating the Stage 23 tables.
from app.models.user import User  # noqa: F401
from app.models.exam import Exam  # noqa: F401
from app.models.question import Question  # noqa: F401
from app.models.sheet import Sheet  # noqa: F401
from app.models.assignment import Assignment  # noqa: F401
from app.models.answer_segments import AnswerSegment  # noqa: F401
from app.models.page_text import PageText  # noqa: F401
from app.models.sheet_pages import SheetPage  # noqa: F401
from app.models.mark import Mark  # noqa: F401
from app.models.flag import Flag  # noqa: F401
from app.models.ai_suggestion import AISuggestion  # noqa: F401
from app.models.audit import AuditLog  # noqa: F401
from app.models.moderation import Moderation  # noqa: F401


def migrate_stage23():
    Base.metadata.create_all(bind=engine)
    print("Stage 23 moderation tables created/verified")


if __name__ == "__main__":
    migrate_stage23()
