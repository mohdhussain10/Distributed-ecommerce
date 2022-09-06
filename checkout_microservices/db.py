import sqlite3

conn = sqlite3.connect("database.db")
print("Opened database successfully")

conn.execute("CREATE TABLE IF NOT EXISTS cart (id INTEGER PRIMARY KEY, user_id INTEGER, items TEXT)")
print("Cart table created successfully")

# conn.execute("DROP TABLE cart")
# print("Cart table dropped.")

conn.close()