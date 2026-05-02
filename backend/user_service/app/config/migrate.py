from sqlalchemy import text

from app.config.database import engine


def ensure_users_avatar_columns() -> None:
    with engine.begin() as conn:
        row = conn.execute(text("SHOW COLUMNS FROM users LIKE 'avatar_blob'")).fetchone()
        if not row:
            conn.execute(
                text(
                    "ALTER TABLE users ADD COLUMN avatar_blob MEDIUMBLOB NULL, "
                    "ADD COLUMN avatar_mime VARCHAR(64) NULL"
                )
            )
        row_url = conn.execute(text("SHOW COLUMNS FROM users LIKE 'avatar_url'")).fetchone()
        if row_url:
            conn.execute(text("ALTER TABLE users DROP COLUMN avatar_url"))
