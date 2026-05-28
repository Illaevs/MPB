from app.services.user_two_factor_bootstrap import ensure_user_two_factor_schema


if __name__ == "__main__":
    ensure_user_two_factor_schema()
    print("user two-factor schema ensured")
