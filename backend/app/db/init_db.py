from app.db.database import engine
from app.db.base import Base

# Import models so SQLAlchemy knows about them
from app.models import User


def init_db():
    Base.metadata.create_all(bind=engine)