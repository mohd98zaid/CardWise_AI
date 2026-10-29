"""CLI script to explicitly provision an administrator out-of-band.

Usage:
    python scripts/provision_admin.py --email admin@example.com --password YourSecurePassword123 --role admin
"""

import argparse
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.db.database import SessionLocal  # noqa: E402
from app.services.admin import provision_admin_user  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Provision an administrative user for CardWise AI.")
    parser.add_argument("--email", required=True, help="Administrator email address")
    parser.add_argument("--password", required=True, help="Administrator password (min 8 chars)")
    parser.add_argument("--role", default="admin", choices=["admin", "reviewer"], help="Privileged role")

    args = parser.parse_args()

    if len(args.password) < 8:
        print("Error: Password must be at least 8 characters long.", file=sys.stderr)
        sys.exit(1)

    with SessionLocal() as db:
        user = provision_admin_user(db, args.email, args.password, role=args.role)
        print(f"Successfully provisioned user '{user.email}' with role '{user.role}' (ID: {user.id}).")


if __name__ == "__main__":
    main()
