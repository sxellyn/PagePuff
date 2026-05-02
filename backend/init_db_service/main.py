import time
import pymysql
import os
import bcrypt
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
        except Exception as e:
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
                    if "already exists" not in str(e).lower():
                        print(f"Error executing: {statement[:50]}... - {e}")
        conn.commit()
        cursor.close()
        print(f"Executed: {file_path.name}")
    except Exception as e:
        print(f"Error executing {file_path}: {e}")

def create_demo_users(conn):
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE username LIKE 'demo_user_%'")
        demo_count = cursor.fetchone()[0]
        
        if demo_count > 0:
            print(f"Demo users already exist ({demo_count} users)")
            cursor.close()
            return
        
        print("Creating demo user groups...")
        
        password = "demo123"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        groups = [
            {"users": ["demo_user_1", "demo_user_2", "demo_user_3"], "criteria": "rating >= 4.5 AND year >= 2015"},
            {"users": ["demo_user_4", "demo_user_5", "demo_user_6"], "criteria": "year BETWEEN 2000 AND 2010"},
            {"users": ["demo_user_7", "demo_user_8", "demo_user_9"], "criteria": "(tags LIKE '%Action%' OR tags LIKE '%Adventure%')"},
            {"users": ["demo_user_10", "demo_user_11", "demo_user_12"], "criteria": "(tags LIKE '%Romance%' OR tags LIKE '%Drama%')"},
            {"users": ["demo_user_13", "demo_user_14", "demo_user_15"], "criteria": "rating BETWEEN 3.5 AND 4.0"},
            {"users": ["demo_user_16", "demo_user_17", "demo_user_18"], "criteria": "year BETWEEN 1990 AND 2000"},
            {"users": ["demo_user_19", "demo_user_20", "demo_user_21"], "criteria": "(tags LIKE '%Comedy%' OR tags LIKE '%Slice of Life%')"},
            {"users": ["demo_user_22", "demo_user_23", "demo_user_24"], "criteria": "rating >= 4.8"},
            {"users": ["demo_user_25", "demo_user_26", "demo_user_27"], "criteria": "(tags LIKE '%Horror%' OR tags LIKE '%Thriller%')"},
            {"users": ["demo_user_28", "demo_user_29", "demo_user_30"], "criteria": "1=1"},
        ]
        
        user_ids = {}
        
        for group in groups:
            for username in group["users"]:
                email = username.replace("_", "") + "@pagepuff.com"
                try:
                    cursor.execute(
                        "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                        (username, email, hashed)
                    )
                    user_id = cursor.lastrowid
                    user_ids[username] = user_id
                except pymysql.err.IntegrityError:
                    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                    result = cursor.fetchone()
                    if result:
                        user_ids[username] = result[0]
        
        conn.commit()
        print(f"Created {len(user_ids)} demo users")
        
        total_favorites_added = 0
        for group in groups:
            try:
                query = f"SELECT id FROM mangas WHERE {group['criteria']} LIMIT 10"
                cursor.execute(query)
                manga_ids = [row[0] for row in cursor.fetchall()]
            except Exception as e:
                print(f"Error searching mangas with criteria '{group['criteria']}': {e}")
                manga_ids = []
            
            if not manga_ids:
                cursor.execute("SELECT id FROM mangas ORDER BY RAND() LIMIT 10")
                manga_ids = [row[0] for row in cursor.fetchall()]
            
            if not manga_ids:
                print(f"No mangas found in database!")
                continue
            
            for username in group["users"]:
                if username in user_ids:
                    user_id = user_ids[username]
                    import random
                    user_manga_ids = random.sample(manga_ids, min(5, len(manga_ids)))
                    
                    for manga_id in user_manga_ids:
                        try:
                            cursor.execute(
                                "INSERT INTO favorites (user_id, manga_id) VALUES (%s, %s)",
                                (user_id, manga_id)
                            )
                            total_favorites_added += 1
                        except pymysql.err.IntegrityError:
                            pass
        
        conn.commit()
        print(f"Favorites added: {total_favorites_added} favorites for user groups")
        
        users_without_favs = []
        for username in user_ids:
            user_id = user_ids[username]
            cursor.execute("SELECT COUNT(*) FROM favorites WHERE user_id = %s", (user_id,))
            fav_count = cursor.fetchone()[0]
            if fav_count == 0:
                users_without_favs.append(username)
                print(f"User {username} (ID: {user_id}) has no favorites!")
        
        if users_without_favs:
            print(f"{len(users_without_favs)} users without favorites: {', '.join(users_without_favs[:5])}")
            cursor.execute("SELECT id FROM mangas ORDER BY RAND() LIMIT 20")
            all_manga_ids = [row[0] for row in cursor.fetchall()]
            
            for username in users_without_favs:
                if username in user_ids and all_manga_ids:
                    user_id = user_ids[username]
                    import random
                    user_manga_ids = random.sample(all_manga_ids, min(5, len(all_manga_ids)))
                    for manga_id in user_manga_ids:
                        try:
                            cursor.execute(
                                "INSERT INTO favorites (user_id, manga_id) VALUES (%s, %s)",
                                (user_id, manga_id)
                            )
                            total_favorites_added += 1
                        except pymysql.err.IntegrityError:
                            pass
            
            conn.commit()
            print(f"Added additional favorites for {len(users_without_favs)} users")
        
        cursor.execute("SELECT COUNT(*) FROM favorites")
        total_favs = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM favorites")
        users_with_favs = cursor.fetchone()[0]
        print(f"Final statistics: {total_favs} favorites from {users_with_favs} users")
        
        cursor.close()
        
    except Exception as e:
        print(f"Error creating demo users: {e}")
        import traceback
        traceback.print_exc()

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
            populate_file = Path("/init-scripts/MANGAPOPULATE.sql")
            if populate_file.exists():
                print("Populating database...")
                execute_sql_file(conn, populate_file)
        
        create_demo_users(conn)
        
        conn.close()
        print("Initialization completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
