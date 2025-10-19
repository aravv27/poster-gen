# server_render.py
import sqlite3
from datetime import datetime
from typing import Optional, Dict

class RenderDatabase:
    def __init__(self, db_path: str = "rendered_images.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with images table supporting phases"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rendered_images (
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
    
    def save_image(self, job_id: str, image_bytes: bytes, width: int, height: int, 
                   phase: str = "assets", image_format: str = 'png'):
        """Save or update rendered image for a specific phase"""
        file_size = len(image_bytes)
        
        with sqlite3.connect(self.db_path) as conn:
            # Try to update existing record
            cursor = conn.execute("""
                UPDATE rendered_images 
                SET image_data = ?, width = ?, height = ?, 
                    image_format = ?, file_size = ?, created_at = CURRENT_TIMESTAMP
                WHERE job_id = ? AND phase = ?
            """, (image_bytes, width, height, image_format, file_size, job_id, phase))
            
            # If no rows updated, insert new record
            if cursor.rowcount == 0:
                conn.execute("""
                    INSERT INTO rendered_images 
                    (job_id, phase, image_data, width, height, image_format, file_size)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (job_id, phase, image_bytes, width, height, image_format, file_size))
            
            conn.commit()
    
    def get_image(self, job_id: str, phase: str = "assets") -> Optional[Dict]:
        """Get rendered image for a specific phase"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT image_data, width, height, image_format, file_size, created_at
                FROM rendered_images 
                WHERE job_id = ? AND phase = ?
            """, (job_id, phase))
            
            row = cursor.fetchone()
            if row:
                return {
                    'image_data': row[0],
                    'width': row[1],
                    'height': row[2],
                    'image_format': row[3],
                    'file_size': row[4],
                    'created_at': row[5]
                }
        return None
    
    def get_all_images(self, job_id: str) -> Dict[str, Dict]:
        """Get all rendered images for all phases"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT phase, image_data, width, height, image_format, file_size, created_at
                FROM rendered_images 
                WHERE job_id = ?
                ORDER BY 
                    CASE phase 
                        WHEN 'layout' THEN 1 
                        WHEN 'canvas' THEN 2 
                        WHEN 'background' THEN 3 
                        WHEN 'assets' THEN 4 
                    END
            """, (job_id,))
            
            results = {}
            for row in cursor.fetchall():
                results[row['phase']] = {
                    'image_data': row['image_data'],
                    'width': row['width'],
                    'height': row['height'],
                    'image_format': row['image_format'],
                    'file_size': row['file_size'],
                    'created_at': row['created_at']
                }
            
            return results
    
    def get_rendered_phases(self, job_id: str) -> Dict[str, bool]:
        """Get which phases have been rendered"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT phase FROM rendered_images WHERE job_id = ?
            """, (job_id,))
            
            rendered_phases = [row[0] for row in cursor.fetchall()]
            
            return {
                'layout': 'layout' in rendered_phases,
                'canvas': 'canvas' in rendered_phases,
                'background': 'background' in rendered_phases,
                'assets': 'assets' in rendered_phases
            }
    
    def delete_image(self, job_id: str, phase: Optional[str] = None):
        """Delete rendered image(s) for a job"""
        with sqlite3.connect(self.db_path) as conn:
            if phase:
                conn.execute("DELETE FROM rendered_images WHERE job_id = ? AND phase = ?", 
                           (job_id, phase))
            else:
                conn.execute("DELETE FROM rendered_images WHERE job_id = ?", (job_id,))
            conn.commit()
