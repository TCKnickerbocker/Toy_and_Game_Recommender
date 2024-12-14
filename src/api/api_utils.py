import os
import sys
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

def setup_connection():
    try:
        conn = snowflake.connector.connect(
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA")
        )
        return conn
    except snowflake.connector.Error as e:
        print(f"Error connecting to Snowflake: {e}", file=sys.stderr)
        raise

def check_user_exists(user_id):
    try:
        conn = setup_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM user_accounts WHERE user_id = %s", (user_id,))
        results = cur.fetchall()
        return len(results) > 0
    except snowflake.connector.Error as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()
    return False

def check_rating_exists(user_id, product_id):
    try:
        conn = setup_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM user_ratings WHERE user_id = %s AND parent_asin = %s", (user_id, product_id))
        results = cur.fetchall()
        return len(results) > 0
    except snowflake.connector.Error as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()
    return False

def check_user_rating_threshold(user_id):
    try:
        conn = setup_connection()
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM user_ratings
            WHERE user_id IN (
                SELECT user_id
                FROM user_ratings
                GROUP BY user_id
                HAVING COUNT(*) > 100
            )
            AND user_id = %s;
            """, (user_id,))
        conn.commit()
    except snowflake.connector.Error as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()
    return
