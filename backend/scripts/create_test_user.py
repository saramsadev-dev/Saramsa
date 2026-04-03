import argparse
import os
import secrets
import string
import sys


DOTENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))


def _load_dotenv(path):
    if not os.path.exists(path):
        return {}
    data = {}
    with open(path, "r", encoding="utf-8") as f:
        for raw in f.readlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def _write_dotenv(path, updates):
    existing = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            existing = f.readlines()

    new_lines = []
    updated_keys = set()
    for raw in existing:
        line = raw.rstrip("\n")
        if not line or line.strip().startswith("#") or "=" not in line:
            new_lines.append(line)
            continue
        key, _ = line.split("=", 1)
        key = key.strip()
        if key in updates:
            new_lines.append(f"{key}={updates[key]}")
            updated_keys.add(key)
        else:
            new_lines.append(line)

    for key, value in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={value}")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines).rstrip("\n") + "\n")


def _generate_password(length=16):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*_-"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def main():
    parser = argparse.ArgumentParser(description="Create or ensure a test user exists.")
    parser.add_argument("--email", help="Email for the test user.")
    parser.add_argument("--password", help="Password for the test user.")
    parser.add_argument("--first-name", default="Test", help="First name.")
    parser.add_argument("--last-name", default="User", help="Last name.")
    parser.add_argument("--role", default="user", help="Role for the user.")
    args = parser.parse_args()

    env = _load_dotenv(DOTENV_PATH)

    email = args.email or env.get("TEST_USER_EMAIL") or "test.user@saramsa.local"
    password = args.password or env.get("TEST_USER_PASSWORD") or _generate_password()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apis.settings")
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
    try:
        import django
        django.setup()
    except Exception as e:
        raise SystemExit(f"Failed to initialize Django: {e}")

    from authentication.services import get_authentication_service

    auth_service = get_authentication_service()
    existing = auth_service.get_user_by_email(email)
    if existing:
        print(f"User already exists: {email}")
    else:
        auth_service.create_user(
            email=email,
            password=password,
            first_name=args.first_name,
            last_name=args.last_name,
            role=args.role,
        )
        print(f"Created user: {email}")

    _write_dotenv(DOTENV_PATH, {
        "TEST_USER_EMAIL": email,
        "TEST_USER_PASSWORD": password,
        "LOGIN_EMAIL": email,
        "LOGIN_PASSWORD": password,
    })

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
