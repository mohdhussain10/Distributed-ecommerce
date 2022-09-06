import sqlite3

conn = sqlite3.connect("database.db")
print("Opened database successfully")

conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price REAL, quantity INTEGER)")
print("Products table created successfully")

conn.close()