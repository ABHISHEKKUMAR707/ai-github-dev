from datetime import datetime, date
from typing import List, Dict, Optional
from .models import AttendanceDatabase, AttendanceRecord

class AttendanceTracker:
    def __init__(self, db_path: str = "attendance.db"):
        self.db = AttendanceDatabase(db_path)
    
    def mark_attendance(self, user_id: str, status: str = "present", timestamp: Optional[datetime] = None) -> bool:
        """
        Mark attendance for a user
        
        Args:
            user_id: Unique identifier for the user
            status: Attendance status ('present', 'absent', 'late')
            timestamp: When attendance was marked (defaults to now)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not user_id or not user_id.strip():
            return False
        
        if status not in ['present', 'absent', 'late']:
            status = 'present'
        
        if timestamp is None:
            timestamp = datetime.now()
        
        record = AttendanceRecord(
            user_id=user_id.strip(),
            timestamp=timestamp,
            status=status
        )
        
        return self.db.insert_attendance(record)
    
    def get_attendance(self, user_id: Optional[str] = None, date_filter: Optional[str] = None) -> List[Dict]:
        """
        Get attendance records
        
        Args:
            user_id: Filter by specific user (optional)
            date_filter: Filter by specific date in YYYY-MM-DD format (optional)
        
        Returns:
            List of attendance records
        """
        if user_id and date_filter:
            # Get specific user's attendance for specific date
            user_records = self.db.get_attendance_by_user(user_id)
            return [record for record in user_records if record['date'] == date_filter]
        elif user_id:
            # Get all attendance for specific user
            return self.db.get_attendance_by_user(user_id)
        elif date_filter:
            # Get all attendance for specific date
            return self.db.get_attendance_by_date(date_filter)
        else:
            # Get all attendance records
            return self.db.get_all_attendance()
    
    def get_attendance_summary(self, user_id: Optional[str] = None) -> Dict:
        """
        Get attendance summary with counts
        
        Args:
            user_id: Filter by specific user (optional)
        
        Returns:
            Dictionary with attendance statistics
        """
        records = self.get_attendance(user_id)
        
        summary = {
            'total_days': len(records),
            'present': 0,
            'absent': 0,
            'late': 0,
            'attendance_rate': 0.0
        }
        
        for record in records:
            status = record['status']
            if status in summary:
                summary[status] += 1
        
        if summary['total_days'] > 0:
            summary['attendance_rate'] = round(
                (summary['present'] + summary['late']) / summary['total_days'] * 100, 2
            )
        
        return summary
    
    def get_users_present_today(self) -> List[str]:
        """
        Get list of users marked present today
        
        Returns:
            List of user IDs who are present today
        """
        today = date.today().strftime("%Y-%m-%d")
        today_records = self.get_attendance(date_filter=today)
        
        present_users = []
        for record in today_records:
            if record['status'] in ['present', 'late']:
                present_users.append(record['user_id'])
        
        return present_users
    
    def is_user_present_today(self, user_id: str) -> bool:
        """
        Check if a specific user is marked present today
        
        Args:
            user_id: User to check
        
        Returns:
            bool: True if user is present today, False otherwise
        """
        today = date.today().strftime("%Y-%m-%d")
        user_today = self.get_attendance(user_id=user_id, date_filter=today)
        
        if user_today:
            return user_today[0]['status'] in ['present', 'late']
        
        return False