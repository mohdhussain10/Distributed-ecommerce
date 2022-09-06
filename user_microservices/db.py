import sqlite3

conn = sqlite3.connect("database.db")
print("Opened database successfully")

conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, wishlist TEXT)")
print("Users table created successfully")

conn.close()