"""Create the Stage 25 results table using the project's SQLAlchemy models."""

from app.db.base import Base
from app.db.database import engine

# Import referenced models so SQLAlchemy can resolve all foreign keys in metadata.
from app.models.exam import Exam  # noqa: F401,E402
from app.models.identity import IdentityMap  # noqa: F401,E402
from app.models.result import Result  # noqa: F401,E402
from app.models.sheet import Sheet  # noqa: F401,E402
from app.models.user import User  # noqa: F401,E402


if __name__ == "__main__":
    Result.__table__.create(bind=engine, checkfirst=True)
    print("Stage 25 results table created/verified")
