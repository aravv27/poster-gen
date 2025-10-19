import sqlite3
conn = sqlite3.connect("rendered_images.db")

# Drop the old table (if exists)
conn.execute("DROP TABLE IF EXISTS rendered_images")

# Create new table with phase column
conn.execute("""
    CREATE TABLE rendered_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL,
        phase TEXT NOT NULL,
        image_data BLOB NOT NULL,
        width INTEGER NOT NULL,
        height INTEGER NOT NULL,
        image_format TEXT NOT NULL DEFAULT 'png',
        file_size INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(job_id, phase)
    )
""")
conn.commit()
conn.close()
