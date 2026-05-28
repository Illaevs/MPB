from app.database.base import Base
from app.database.session import engine_sync
from app.models.task_user_matrix import TaskUserMatrix


def ensure_task_matrix_schema() -> None:
    Base.metadata.create_all(engine_sync, tables=[TaskUserMatrix.__table__])
