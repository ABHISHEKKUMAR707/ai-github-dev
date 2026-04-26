from datetime import datetime
from typing import List, Dict, Optional
import sqlite3
import os

class AttendanceRecord:
    def __init__(self, user_id: str, timestamp: datetime, status: str = "present"):
        self.user_id = user_id
        self.timestamp = timestamp
        self.status = status

class AttendanceDatabase:
    def __init__(self, db_path: str = "attendance.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT DEFAULT 'present',
                    date TEXT NOT NULL,
                    UNIQUE(user_id, date)
                )
            """)
            conn.commit()
    
    def insert_attendance(self, record: AttendanceRecord) -> bool:
        """Insert an attendance record"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                date_str = record.timestamp.strftime("%Y-%m-%d")
                timestamp_str = record.timestamp.isoformat()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO attendance 
                    (user_id, timestamp, status, date) 
                    VALUES (?, ?, ?, ?)
                """, (record.user_id, timestamp_str, record.status, date_str))
                conn.commit()
                return True
        except sqlite3.Error:
            return False
    
    def get_attendance_by_user(self, user_id: str) -> List[Dict]:
        """Get all attendance records for a specific user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, timestamp, status, date 
                FROM attendance 
                WHERE user_id = ? 
                ORDER BY timestamp DESC
            """, (user_id,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'user_id': row[0],
                    'timestamp': datetime.fromisoformat(row[1]),
                    'status': row[2],
                    'date': row[3]
                })
            return results
    
    def get_attendance_by_date(self, date: str) -> List[Dict]:
        """Get all attendance records for a specific date"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, timestamp, status, date 
                FROM attendance 
                WHERE date = ? 
                ORDER BY timestamp ASC
            """, (date,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'user_id': row[0],
                    'timestamp': datetime.fromisoformat(row[1]),
                    'status': row[2],
                    'date': row[3]
                })
            return results
    
    def get_all_attendance(self) -> List[Dict]:
        """Get all attendance records"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, timestamp, status, date 
                FROM attendance 
                ORDER BY timestamp DESC
            """)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'user_id': row[0],
                    'timestamp': datetime.fromisoformat(row[1]),
                    'status': row[2],
                    'date': row[3]
                })
            return results