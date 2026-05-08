from sqlalchemy import UUID, Column, ForeignKey, String

from .base import AuditMixin, Base, DescriptionMixin, IDMixin


class SubTask(IDMixin, AuditMixin, DescriptionMixin, Base):
    __tablename__ = "kvs_sub_tasks"

    name = Column(String(250), unique=False, index=False, nullable=False)
    status = Column(String(50), unique=False, index=False, nullable=False)
    object_type = Column(String(50), unique=False, index=False, nullable=False)
    object_id = Column(String(50), unique=False, index=False, nullable=True)
    action = Column(String(50), unique=False, index=False, nullable=False)
    attempt = Column(String(25), unique=False, index=False, nullable=False)
    parent_task = Column(
        UUID(as_uuid=True), ForeignKey("kvs_tasks.id"), nullable=False
    )
    response_code = Column(String(10), unique=False, index=False, nullable=True)
    response_message = Column(
        String(500), unique=False, index=False, nullable=True
    )

    job_id = Column(String(100), unique=False, index=False, nullable=True)
