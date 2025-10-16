import sqlite3
from typing import Optional, Dict
class RenderDatabase:
    """Separate database for storing rendered images"""
    
    def __init__(self, db_path: str = "rendered_images.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the rendered images database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rendered_images (
                    job_id TEXT PRIMARY KEY,
                    image_data BLOB NOT NULL,
                    image_format TEXT DEFAULT 'png',
                    width INTEGER,
                    height INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_size INTEGER
                )
            """)
            conn.commit()
    
    def save_image(self, job_id: str, image_bytes: bytes, width: int, height: int, image_format: str = "png"):
        """Save rendered image to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO rendered_images 
                (job_id, image_data, image_format, width, height, file_size)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (job_id, image_bytes, image_format, width, height, len(image_bytes)))
            conn.commit()
    
    def get_image(self, job_id: str) -> Optional[Dict]:
        """Retrieve rendered image from database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT job_id, image_data, image_format, width, height, file_size, created_at
                FROM rendered_images 
                WHERE job_id = ?
            """, (job_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'job_id': row['job_id'],
                    'image_data': row['image_data'],
                    'image_format': row['image_format'],
                    'width': row['width'],
                    'height': row['height'],
                    'file_size': row['file_size'],
                    'created_at': row['created_at']
                }
        return None
    
    def delete_image(self, job_id: str):
        """Delete rendered image from database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM rendered_images WHERE job_id = ?", (job_id,))
            conn.commit()
