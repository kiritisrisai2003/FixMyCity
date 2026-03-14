"""
Complaint Manager - Handles complaint storage and retrieval
Uses SQLite for better data management
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import uuid

class ComplaintManager:
    def __init__(self, db_path: str = "data/complaints.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database"""
        import os
        os.makedirs("data", exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                location TEXT NOT NULL,
                category TEXT NOT NULL,
                citizen_mobile TEXT NOT NULL,
                citizen_name TEXT NOT NULL,
                additional_answers TEXT,
                image_path TEXT,
                image_validation TEXT,
                ai_analysis TEXT,
                status TEXT DEFAULT 'submitted',
                assigned_to TEXT,
                resolution_remarks TEXT,
                reraise_count INTEGER DEFAULT 0,
                reraise_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_id TEXT NOT NULL,
                old_status TEXT,
                new_status TEXT NOT NULL,
                remarks TEXT,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (complaint_id) REFERENCES complaints (id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_complaint(self, complaint_data: Dict) -> str:
        """Create a new complaint"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        complaint_id = f"CMP{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        
        cursor.execute("""
            INSERT INTO complaints (
                id, description, location, category, citizen_mobile, citizen_name,
                additional_answers, image_path, image_validation, ai_analysis, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            complaint_id,
            complaint_data["description"],
            complaint_data["location"],
            complaint_data["category"],
            complaint_data["citizenMobile"],
            complaint_data["citizenName"],
            json.dumps(complaint_data.get("additionalAnswers", {})),
            complaint_data.get("imagePath"),
            json.dumps(complaint_data.get("imageValidation")) if complaint_data.get("imageValidation") else None,
            json.dumps(complaint_data["aiAnalysis"]),
            complaint_data.get("status", "submitted")
        ))
        
        conn.commit()
        conn.close()
        
        return complaint_id
    
    def get_complaints(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get complaints with filters"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM complaints WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        complaints = []
        for row in rows:
            complaint = dict(row)
            
            # Parse JSON fields
            if complaint["additional_answers"]:
                complaint["additionalAnswers"] = json.loads(complaint["additional_answers"])
            if complaint["image_validation"]:
                complaint["imageValidation"] = json.loads(complaint["image_validation"])
            if complaint["ai_analysis"]:
                complaint["aiAnalysis"] = json.loads(complaint["ai_analysis"])
            
            # Format for frontend
            complaint["complaintId"] = complaint["id"]
            complaint["citizenMobile"] = complaint["citizen_mobile"]
            complaint["citizenName"] = complaint["citizen_name"]
            complaint["imagePath"] = complaint["image_path"]
            complaint["timestamp"] = complaint["created_at"]
            
            complaints.append(complaint)
        
        conn.close()
        return complaints
    
    def get_complaint_by_id(self, complaint_id: str) -> Optional[Dict]:
        """Get a specific complaint"""
        complaints = self.get_complaints()
        for complaint in complaints:
            if complaint["id"] == complaint_id:
                return complaint
        return None
    
    def update_status(self, complaint_id: str, new_status: str, remarks: str = "") -> bool:
        """Update complaint status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current status
        cursor.execute("SELECT status FROM complaints WHERE id = ?", (complaint_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return False
        
        old_status = row[0]
        
        # Update complaint
        update_query = """
            UPDATE complaints 
            SET status = ?, updated_at = CURRENT_TIMESTAMP, resolution_remarks = ?
        """
        params = [new_status, remarks]
        
        if new_status == "resolved":
            update_query += ", resolved_at = CURRENT_TIMESTAMP"
        
        update_query += " WHERE id = ?"
        params.append(complaint_id)
        
        cursor.execute(update_query, params)
        
        # Log status change
        cursor.execute("""
            INSERT INTO status_history (complaint_id, old_status, new_status, remarks)
            VALUES (?, ?, ?, ?)
        """, (complaint_id, old_status, new_status, remarks))
        
        conn.commit()
        conn.close()
        
        return True
    
    def reraise_complaint(self, complaint_id: str, reason: str) -> bool:
        """Reraise a resolved complaint"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if complaint can be reraised (resolved within 3 days)
        cursor.execute("""
            SELECT status, resolved_at, reraise_count 
            FROM complaints 
            WHERE id = ?
        """, (complaint_id,))
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return False
        
        status, resolved_at, reraise_count = row
        
        if status != "resolved":
            conn.close()
            return False
        
        # Check 3-day window
        if resolved_at:
            resolved_date = datetime.fromisoformat(resolved_at)
            if datetime.now() - resolved_date > timedelta(days=3):
                conn.close()
                return False
        
        # Reraise complaint
        cursor.execute("""
            UPDATE complaints 
            SET status = 'reopened', 
                reraise_count = ?,
                reraise_reason = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (reraise_count + 1, reason, complaint_id))
        
        # Log in history
        cursor.execute("""
            INSERT INTO status_history (complaint_id, old_status, new_status, remarks)
            VALUES (?, ?, ?, ?)
        """, (complaint_id, "resolved", "reopened", f"Reraised: {reason}"))
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_trend_data(self, days: int = 7) -> List[Dict]:
        """Get complaint trend data for last N days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get data for last N days
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM complaints
            WHERE created_at >= date('now', '-' || ? || ' days')
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (days,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Fill missing dates with 0
        trend_data = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=days-i-1)).strftime("%Y-%m-%d")
            count = 0
            
            for row in rows:
                if row[0] == date:
                    count = row[1]
                    break
            
            trend_data.append({
                "date": date,
                "count": count,
                "label": (datetime.now() - timedelta(days=days-i-1)).strftime("%a")
            })
        
        return trend_data
    
    def get_statistics(self) -> Dict:
        """Get overall statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total complaints
        cursor.execute("SELECT COUNT(*) FROM complaints")
        total = cursor.fetchone()[0]
        
        # By status
        cursor.execute("""
            SELECT status, COUNT(*) 
            FROM complaints 
            GROUP BY status
        """)
        status_counts = dict(cursor.fetchall())
        
        # By category
        cursor.execute("""
            SELECT category, COUNT(*) 
            FROM complaints 
            GROUP BY category
        """)
        category_counts = dict(cursor.fetchall())
        
        # Average resolution time
        cursor.execute("""
            SELECT AVG(JULIANDAY(resolved_at) - JULIANDAY(created_at))
            FROM complaints
            WHERE resolved_at IS NOT NULL
        """)
        avg_resolution_days = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "total": total,
            "byStatus": status_counts,
            "byCategory": category_counts,
            "avgResolutionDays": round(avg_resolution_days, 1)
        }