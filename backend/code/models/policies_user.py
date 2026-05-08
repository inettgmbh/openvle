from sqlalchemy import UUID, Column, ForeignKey, UniqueConstraint

from .base import AuditMixin, Base, IDMixin


class PoliciesUser(IDMixin, AuditMixin, Base):
    __tablename__ = "sys_policies_user"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("sys_users.id"), nullable=False
    )
    policy_id = Column(
        UUID(as_uuid=True), ForeignKey("sys_policies.id"), nullable=False
    )

    __table_args__ = (UniqueConstraint(user_id, policy_id),)
