import snowflake.connector
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Connect to Snowflake using variables from .env
conn = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account=os.getenv("SNOWFLAKE_ACCOUNT"), # questionable
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database=os.getenv("SNOWFLAKE_DATABASE"),
    schema=os.getenv("SNOWFLAKE_SCHEMA")  # questionable
)

# Cursor to execute SQL
cur = conn.cursor()

# Query to get the first 10 results
cur.execute("SELECT * FROM TOYS_AND_GAMES_REVIEWS LIMIT 10")
results = cur.fetchall()

# Print results
for row in results:
    print(row)

# Close connections
cur.close()
conn.close()
