from app.services.user_avatar_bootstrap import ensure_user_avatar_schema


if __name__ == "__main__":
    ensure_user_avatar_schema()
    print("User avatar schema created or updated successfully!")
