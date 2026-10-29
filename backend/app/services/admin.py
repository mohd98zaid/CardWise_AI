"""Administrative user provisioning service."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import AuditEvent, User

_logger = logging.getLogger("cardwise.admin")


def provision_admin_user(
    db: Session,
    email: str,
    password: str,
    role: str = "admin",
) -> User:
    """Explicitly provision an administrative user out-of-band."""
    normalized_email = email.strip().lower()
    if role not in {"admin", "reviewer"}:
        raise ValueError(f"Invalid privileged role: {role}")

    user = db.scalar(select(User).where(User.email == normalized_email))
    if user is not None:
        user.role = role
        user.password_hash = hash_password(password)
        user.status = "active"
        _logger.info("Updated existing user %s to privileged role %s", normalized_email, role)
    else:
        user = User(
            email=normalized_email,
            password_hash=hash_password(password),
            role=role,
            status="active",
        )
        db.add(user)
        db.flush()
        _logger.info("Provisioned new privileged user %s with role %s", normalized_email, role)

    db.add(
        AuditEvent(
            actor_id="system_provisioning",
            action=f"provision_{role}",
            entity_type="user",
            entity_id=user.id,
            metadata_json={"email": normalized_email, "role": role},
        )
    )
    db.commit()
    db.refresh(user)
    return user
