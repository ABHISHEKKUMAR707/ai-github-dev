from datetime import datetime, date
from typing import List, Optional
import sqlite3
import os

class AttendanceRecord:
    """Model for attendance records."""
    
    DB_PATH = 'attendance.db'
    
    def __init__(self, user_id: int, status: str, timestamp: datetime, record_id: Optional[int] = None):
        """
        Initialize an attendance record.
        
        Args:
            user_id: The ID of the user
            status: Attendance status ('present', 'absent', 'late')
            timestamp: Timestamp of the attendance record
            record_id: Optional record ID for existing records
        """
        self.id = record_id
        self.user_id = user_id
        self.status = status
        self.timestamp = timestamp
        
        # Initialize database if it doesn't exist
        self._init_db()
    
    @classmethod
    def _init_db(cls):
        """Initialize the database and create tables if they don't exist."""
        try:
            conn = sqlite3.connect(cls.DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_date 
                ON attendance_records(user_id, DATE(timestamp))
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error initializing database: {e}")
    
    def save(self) -> bool:
        """
        Save the attendance record to the database.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            
            if self.id is None:
                # Insert new record
                cursor.execute('''
                    INSERT INTO attendance_records (user_id, status, timestamp)
                    VALUES (?, ?, ?)
                ''', (self.user_id, self.status, self.timestamp))
                self.id = cursor.lastrowid
            else:
                # Update existing record
                cursor.execute('''
                    UPDATE attendance_records 
                    SET user_id = ?, status = ?, timestamp = ?
                    WHERE id = ?
                ''', (self.user_id, self.status, self.timestamp, self.id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving attendance record: {e}")
            return False
    
    @classmethod
    def get_by_user_and_date(cls, user_id: int, target_date: date) -> Optional['AttendanceRecord']:
        """
        Get attendance record for a user on a specific date.
        
        Args:
            user_id: The ID of the user
            target_date: The date to search for
            
        Returns:
            Optional[AttendanceRecord]: The attendance record if found, None otherwise
        """
        try:
            conn = sqlite3.connect(cls.DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, user_id, status, timestamp
                FROM attendance_records
                WHERE user_id = ? AND DATE(timestamp) = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (user_id, target_date.isoformat()))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return cls(
                    record_id=row[0],
                    user_id=row[1],
                    status=row[2],
                    timestamp=datetime.fromisoformat(row[3])
                )
            return None
        except Exception as e:
            print(f"Error getting attendance record: {e}")
            return None
    
    @classmethod
    def get_records(cls, user_id: Optional[int] = None, date: Optional[datetime] = None) -> List['AttendanceRecord']:
        """
        Get attendance records with optional filtering.
        
        Args:
            user_id: Optional user ID to filter by
            date: Optional date to filter by
            
        Returns:
            List[AttendanceRecord]: List of attendance records
        """
        try:
            conn = sqlite3.connect(cls.DB_PATH)
            cursor = conn.cursor()
            
            query = 'SELECT id, user_id, status, timestamp FROM attendance_records WHERE 1=1'
            params = []
            
            if user_id is not None:
                query += ' AND user_id = ?'
                params.append(user_id)
            
            if date is not None:
                query += ' AND DATE(timestamp) = ?'
                params.append(date.date().isoformat())
            
            query += ' ORDER BY timestamp DESC'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            records = []
            for row in rows:
                records.append(cls(
                    record_id=row[0],
                    user_id=row[1],
                    status=row[2],
                    timestamp=datetime.fromisoformat(row[3])
                ))
            
            return records
        except Exception as e:
            print(f"Error getting attendance records: {e}")
            return []
    
    @classmethod
    def get_records_by_date_range(cls, user_id: int, start_date: datetime, end_date: datetime) -> List['AttendanceRecord']:
        """
        Get attendance records for a user within a date range.
        
        Args:
            user_id: The ID of the user
            start_date: Start date of the range
            end_date: End date of the range
            
        Returns:
            List[AttendanceRecord]: List of attendance records
        """
        try:
            conn = sqlite3.connect(cls.DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, user_id, status, timestamp
                FROM attendance_records
                WHERE user_id = ? AND DATE(timestamp) BETWEEN ? AND ?
                ORDER BY timestamp ASC
            ''', (user_id, start_date.date().isoformat(), end_date.date().isoformat()))
            
            rows = cursor.fetchall()
            conn.close()
            
            records = []
            for row in rows:
                records.append(cls(
                    record_id=row[0],
                    user_id=row[1],
                    status=row[2],
                    timestamp=datetime.fromisoformat(row[3])
                ))
            
            return records
        except Exception as e:
            print(f"Error getting attendance records by date range: {e}")
            return []
    
    def delete(self) -> bool:
        """
        Delete the attendance record from the database.
        
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        if self.id is None:
            return False
        
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM attendance_records WHERE id = ?', (self.id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting attendance record: {e}")
            return False