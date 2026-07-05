import time
import pymysql
import os
from pathlib import Path

def wait_for_mysql(max_retries=30):
    for i in range(max_retries):
        try:
            conn = pymysql.connect(
                host=os.getenv("MYSQL_HOST", "mysql"),
                user=os.getenv("MYSQL_USER", "root"),
                password=os.getenv("MYSQL_PASSWORD", "root"),
                database=os.getenv("MYSQL_DATABASE", "pagepuff"),
                connect_timeout=5
            )
            conn.close()
            print("MySQL is ready!")
            return True
        except Exception:
            print(f"Waiting for MySQL... ({i+1}/{max_retries})")
            time.sleep(2)
    return False

def execute_sql_file(conn, file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sql = f.read()

        cursor = conn.cursor()
        for statement in sql.split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                except Exception as e:
                    if "already exists" not in str(e).lower() and "duplicate entry" not in str(e).lower():
                        print(f"Error executing: {statement[:50]}... - {e}")
        conn.commit()
        cursor.close()
        print(f"Executed: {file_path.name}")
    except Exception as e:
        print(f"Error executing {file_path}: {e}")

def main():
    print("Initializing PagePuff database...")

    if not wait_for_mysql():
        print("Could not connect to MySQL")
        return

    try:
        conn = pymysql.connect(
            host=os.getenv("MYSQL_HOST", "mysql"),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", "root"),
            database=os.getenv("MYSQL_DATABASE", "pagepuff"),
            charset='utf8mb4'
        )

        init_file = Path("/init-scripts/init_all_tables.sql")
        if init_file.exists():
            execute_sql_file(conn, init_file)

        cursor = conn.cursor()
        cursor.execute("SHOW COLUMNS FROM users LIKE 'avatar_blob'")
        if not cursor.fetchone():
            try:
                cursor.execute(
                    "ALTER TABLE users ADD COLUMN avatar_blob MEDIUMBLOB NULL, "
                    "ADD COLUMN avatar_mime VARCHAR(64) NULL"
                )
                conn.commit()
                print("Migration: added users.avatar_blob, avatar_mime")
            except Exception as e:
                conn.rollback()
                print(f"Migration avatar_blob: {e}")
        cursor.execute("SHOW COLUMNS FROM users LIKE 'avatar_url'")
        if cursor.fetchone():
            try:
                cursor.execute("ALTER TABLE users DROP COLUMN avatar_url")
                conn.commit()
                print("Migration: dropped legacy users.avatar_url")
            except Exception as e:
                conn.rollback()
                print(f"Migration drop avatar_url: {e}")
        cursor.close()

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM mangas")
        manga_count = cursor.fetchone()[0]
        cursor.close()

        if manga_count == 0:
            populate_file = Path("/init-scripts/populate_demo.sql")
            if populate_file.exists():
                print("Populating demo data...")
                execute_sql_file(conn, populate_file)
            else:
                print("populate_demo.sql not found")

        conn.close()
        print("Initialization completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
