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


# EXAMPLE DATA
# (5.0, 'Cute', 'Blocks are very nice, recommend them.', '[]', 'B01BV03H02', 'B06XCXWBHW', 'AH7N6BGNM7GCMQQZLV3UJ4HL4ELA', datetime.datetime(2018, 7, 18, 19, 59, 7, 977000), 0, True)
# (5.0, 'Son loves it', 'My son enjoys playing with this piano both while doing tummy time or kicking it in the car it keeps him entertained.', '[]', 'B01MCUJR59', 'B01MCUJR59', 'AH7N6BGNM7GCMQQZLV3UJ4HL4ELA', datetime.datetime(2018, 7, 18, 19, 44, 57, 86000), 0, True)
# (5.0, 'My niece loved it', "I got this for niece's birthday and she loved it.", '[]', 'B00ZYDALUM', 'B00ZYDALUM', 'AH7N6BGNM7GCMQQZLV3UJ4HL4ELA', datetime.datetime(2017, 10, 31, 20, 2, 53, 890000), 0, True)
# (5.0, 'Very nice', 'I gave this pack as a gift and she loves it!  Had no problems starting them to sing individually or together.  Recommended this product.', '[]', 'B00NR9XNG4', 'B00NR9XNG4', 'AH7N6BGNM7GCMQQZLV3UJ4HL4ELA', datetime.datetime(2017, 1, 3, 3, 10, 50), 0, True)
# (4.0, 'nice product - great for my hobby time', 'Does not have the avoidance detection I was of the understanding that it had.  nice product  - great for my hobby time.', '[]', 'B01HHVLDQO', 'B01LZKB7DQ', 'AEOH36HL5HNSBRS66NPTUY3NLJKQ', datetime.datetime(2018, 6, 4, 17, 5, 58, 176000), 0, True)
# (5.0, 'Shipped quickly', 'Love the product', '[]', 'B0185H7FN4', 'B0185H7FN4', 'AECDMHEN4FYAC3NWDRYXHP56ME5A', datetime.datetime(2018, 12, 30, 23, 35, 33, 454000), 1, True)
# (5.0, 'Great Stickers', 'They are really nice and peel off easily. Look great on the cards.', '[]', 'B07PFYTMVJ', 'B07PFYTMVJ', 'AG7BUYQZ5DMTO75EKH3JRG7B5D2Q', datetime.datetime(2023, 2, 21, 23, 23, 13, 255000), 0, True)
# (5.0, 'Great Stickers!', 'These are great stickers and peel off very easily without leaving anything behind like some stickers do. I love the different sizes. Just what I needed.', '[]', 'B09LV7FD4C', 'B09LV7FD4C', 'AG7BUYQZ5DMTO75EKH3JRG7B5D2Q', datetime.datetime(2023, 2, 21, 23, 21, 26, 370000), 0, True)
# (5.0, 'Excellent product.', 'I loved the good quality of the coloring posters.  My students had a great time coloring their posters - each student got a different design and they loved the activity.  They remained engaged coloring for more than 35 minutes.  Top 5 stars and I am buying more for next year.', '[]', 'B07VKFSR69', 'B07VKFSR69', 'AEWABKGYKEN5SZECUANUKBTH3LAQ', datetime.datetime(2019, 11, 1, 17, 24, 17, 533000), 1, True)
# (5.0, 'Five Stars', 'Great product!', '[]', 'B01N3U1VZW', 'B01N3U1VZW', 'AFZZJZSIXY72VS56HKGSWB7CVIMQ', datetime.datetime(2018, 6, 10, 18, 9, 7, 12000), 0, True)