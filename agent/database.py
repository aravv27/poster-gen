import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import traceback

class ProjectStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"

class PhaseType(str, Enum):
    LAYOUT = "layout"
    CANVAS = "canvas"
    BACKGROUND = "background"
    ASSETS = "assets"

class DatabaseManager:
    def __init__(self, db_path: str = "poster_generator.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    user_prompt TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    current_phase TEXT NOT NULL DEFAULT 'layout',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS phase_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    json_data TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'partial',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id),
                    UNIQUE(project_id, phase)
                )
            """)
            
            conn.commit()
    
    def create_project(self, user_prompt: str) -> str:
        """Create a new poster project"""
        project_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO projects (id, user_prompt, status, current_phase)
                VALUES (?, ?, ?, ?)
            """, (project_id, user_prompt, ProjectStatus.ACTIVE, PhaseType.LAYOUT))
            conn.commit()
        
        return project_id
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project details"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM projects WHERE id = ?
            """, (project_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None
    
    def update_project_status(self, project_id: str, status: ProjectStatus, current_phase: Optional[PhaseType] = None):
        """Update project status and optionally current phase"""
        with sqlite3.connect(self.db_path) as conn:
            if current_phase:
                conn.execute("""
                    UPDATE projects 
                    SET status = ?, current_phase = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, current_phase, project_id))
            else:
                conn.execute("""
                    UPDATE projects 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, project_id))
            conn.commit()
    
    def save_phase_result(self, project_id: str, phase: PhaseType, json_data: Dict, status: str = "completed"):
        """Save or update phase result JSON"""
        json_string = json.dumps(json_data, indent=2)
        
        with sqlite3.connect(self.db_path) as conn:
            # Try to update existing record first
            cursor = conn.execute("""
                UPDATE phase_results 
                SET json_data = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE project_id = ? AND phase = ?
            """, (json_string, status, project_id, phase))
            
            # If no rows were updated, insert new record
            if cursor.rowcount == 0:
                conn.execute("""
                    INSERT INTO phase_results (project_id, phase, json_data, status)
                    VALUES (?, ?, ?, ?)
                """, (project_id, phase, json_string, status))
            
            conn.commit()
    
    def get_phase_result(self, project_id: str, phase: PhaseType) -> Optional[Dict]:
        """Get phase result JSON"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT json_data, status FROM phase_results 
                WHERE project_id = ? AND phase = ?
            """, (project_id, phase))
            
            row = cursor.fetchone()
            if row:
                return {
                    'json_data': json.loads(row[0]),
                    'status': row[1]
                }
        return None
    
    def get_all_phase_results(self, project_id: str) -> Dict[str, Dict]:
        """Get all phase results for a project"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT phase, json_data, status, updated_at FROM phase_results 
                WHERE project_id = ?
                ORDER BY 
                    CASE phase 
                        WHEN 'layout' THEN 1 
                        WHEN 'canvas' THEN 2 
                        WHEN 'background' THEN 3 
                        WHEN 'assets' THEN 4 
                    END
            """, (project_id,))
            
            results = {}
            for row in cursor.fetchall():
                results[row['phase']] = {
                    'json_data': json.loads(row['json_data']),
                    'status': row['status'],
                    'updated_at': row['updated_at']
                }
            
            return results
    
    def get_latest_phase_result(self, project_id: str) -> Optional[Dict]:
        """Get the latest completed phase result"""
        phases_order = ['assets', 'background', 'canvas', 'layout']
        
        for phase in phases_order:
            result = self.get_phase_result(project_id, PhaseType(phase))
            if result and result['status'] == 'completed':
                return {'phase': phase, **result}
        
        return None
    
    def get_current_json_for_next_phase(self, project_id: str, current_phase: PhaseType) -> Optional[Dict]:
        """Get the JSON that should be used as input for the next phase"""
        phase_order = [PhaseType.LAYOUT, PhaseType.CANVAS, PhaseType.BACKGROUND, PhaseType.ASSETS]
        
        try:
            current_index = phase_order.index(current_phase)
            if current_index == 0:
                # For layout phase, no previous JSON needed
                return None
            
            # Get the previous phase result
            previous_phase = phase_order[current_index - 1]
            result = self.get_phase_result(project_id, previous_phase)
            
            if result and result['status'] == 'completed':
                return result['json_data']
            
        except ValueError:
            pass
        
        return None
    
    def list_projects(self, status: Optional[ProjectStatus] = None) -> List[Dict]:
        """List all projects, optionally filtered by status"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if status:
                cursor = conn.execute("""
                    SELECT * FROM projects WHERE status = ?
                    ORDER BY updated_at DESC
                """, (status,))
            else:
                cursor = conn.execute("""
                    SELECT * FROM projects ORDER BY updated_at DESC
                """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_project(self, project_id: str):
        """Delete a project and all its phase results"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM phase_results WHERE project_id = ?", (project_id,))
            conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
    
    def get_project_progress(self, project_id: str) -> Dict:
        """Get project progress summary"""
        phases = self.get_all_phase_results(project_id)
        project = self.get_project(project_id)
        
        progress = {
            'project_id': project_id,
            'user_prompt': project['user_prompt'] if project else '',
            'status': project['status'] if project else 'unknown',
            'current_phase': project['current_phase'] if project else 'unknown',
            'completed_phases': [],
            'partial_phases': [],
            'total_phases': 4
        }
        
        for phase, result in phases.items():
            if result['status'] == 'completed':
                progress['completed_phases'].append(phase)
            elif result['status'] == 'partial':
                progress['partial_phases'].append(phase)
        
        progress['completion_percentage'] = (len(progress['completed_phases']) / progress['total_phases']) * 100
        
        return progress