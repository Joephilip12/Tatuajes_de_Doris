import os
from sqlalchemy import select

from app.db import SessionLocal
from app.models import AdminUser
from app.models import utcnow
from app.core.security import hash_password

def main() -> None:
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")

    if not email or not password:
        raise SystemExit("Missing ADMIN_EMAIL or ADMIN_PASSWORD env vars.")

    db = SessionLocal()
    try:
        existing = db.execute(select(AdminUser).where(AdminUser.email == email)).scalar_one_or_none()
        if existing:
            print(f"Admin already exists: {email}")
            return

        admin = AdminUser(
            email=email,
            password_hash=hash_password(password),
            is_active=True,
            created_at=utcnow(),
        )
        db.add(admin)
        db.commit()
        print(f"Created admin: {email}")
    finally:
        db.close()

if __name__ == "__main__":
    main()