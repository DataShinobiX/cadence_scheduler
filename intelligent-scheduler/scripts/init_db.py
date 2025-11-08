from app.db.base import Base, engine
from app.models.user import User
from app.models.task import Task
# Import other models...

def init_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    init_db()