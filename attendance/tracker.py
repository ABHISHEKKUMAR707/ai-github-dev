from datetime import datetime
from typing import List, Dict, Optional
from .models import AttendanceRecord

class AttendanceTracker:
    """Class to handle attendance tracking operations."""
    
    def __init__(self):
        """Initialize the attendance tracker."""
        pass
    
    def mark_attendance(self, user_id: int, status: str = 'present', timestamp: Optional[datetime] = None) -> bool:
        """
        Mark attendance for a user.
        
        Args:
            user_id: The ID of the user
            status: Attendance status ('present', 'absent', 'late')
            timestamp: Optional timestamp, defaults to current time
            
        Returns:
            bool: True if attendance was marked successfully, False otherwise
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            # Check if attendance already exists for today
            today = timestamp.date()
            existing_record = AttendanceRecord.get_by_user_and_date(user_id, today)
            
            if existing_record:
                # Update existing record
                existing_record.status = status
                existing_record.timestamp = timestamp
                existing_record.save()
            else:
                # Create new record
                record = AttendanceRecord(
                    user_id=user_id,
                    status=status,
                    timestamp=timestamp
                )
                record.save()
            
            return True
        except Exception as e:
            print(f"Error marking attendance: {e}")
            return False
    
    def get_attendance(self, user_id: Optional[int] = None, date: Optional[datetime] = None) -> List[Dict]:
        """
        Get attendance records.
        
        Args:
            user_id: Optional user ID to filter by
            date: Optional date to filter by
            
        Returns:
            List[Dict]: List of attendance records
        """
        try:
            records = AttendanceRecord.get_records(user_id=user_id, date=date)
            
            attendance_data = []
            for record in records:
                attendance_data.append({
                    'id': record.id,
                    'user_id': record.user_id,
                    'status': record.status,
                    'timestamp': record.timestamp.isoformat() if record.timestamp else None,
                    'date': record.timestamp.date().isoformat() if record.timestamp else None
                })
            
            return attendance_data
        except Exception as e:
            print(f"Error getting attendance: {e}")
            return []
    
    def get_attendance_summary(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """
        Get attendance summary for a user within a date range.
        
        Args:
            user_id: The ID of the user
            start_date: Start date for the summary
            end_date: End date for the summary
            
        Returns:
            Dict: Summary containing counts of different attendance statuses
        """
        try:
            records = AttendanceRecord.get_records_by_date_range(user_id, start_date, end_date)
            
            summary = {
                'total_days': 0,
                'present': 0,
                'absent': 0,
                'late': 0,
                'attendance_rate': 0.0
            }
            
            for record in records:
                summary['total_days'] += 1
                if record.status == 'present':
                    summary['present'] += 1
                elif record.status == 'absent':
                    summary['absent'] += 1
                elif record.status == 'late':
                    summary['late'] += 1
            
            if summary['total_days'] > 0:
                summary['attendance_rate'] = (summary['present'] + summary['late']) / summary['total_days'] * 100
            
            return summary
        except Exception as e:
            print(f"Error getting attendance summary: {e}")
            return {}