import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('example.mbtiles')
cursor = conn.cursor()

# Create a table to store binary data
cursor.execute('''CREATE TABLE IF NOT EXISTS BinaryData (id INTEGER PRIMARY KEY, data BLOB)''')

# Binary data to insert
binary_data = b'\x1aH\n\x05water\x12\x18\x12\x06\x00\x00\x01\x01\x02\x02\x18\x03"\x0c\t\x00\x80@\x1a\x00\x13\x14\x00\x00\x14\x0f\x1a\x03uid\x1a\x03foo\x1a\x03cat"\x02 {"\x05\n\x03bar"\x06\n\x04flew(\x80 x\x02'

# Insert binary data into the database
cursor.execute("INSERT INTO BinaryData (data) VALUES (?)", (binary_data,))
conn.commit()

# Close the connection
conn.close()
