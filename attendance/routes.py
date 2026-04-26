from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, date
from .tracker import AttendanceTracker

# Create blueprint
attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

# Initialize tracker
tracker = AttendanceTracker()

@attendance_bp.route('/')
def index():
    """Render the attendance tracking interface."""
    return render_template('attendance.html')

@attendance_bp.route('/mark', methods=['POST'])
def mark_attendance():
    """Mark attendance for a user."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_id = data.get('user_id')
        status = data.get('status', 'present')
        timestamp_str = data.get('timestamp')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        if status not in ['present', 'absent', 'late']:
            return jsonify({'error': 'Invalid status. Must be present, absent, or late'}), 400
        
        # Parse timestamp if provided
        timestamp = None
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except ValueError:
                return jsonify({'error': 'Invalid timestamp format'}), 400
        
        # Mark attendance
        success = tracker.mark_attendance(user_id, status, timestamp)
        
        if success:
            return jsonify({
                'message': 'Attendance marked successfully',
                'user_id': user_id,
                'status': status,
                'timestamp': (timestamp or datetime.now()).isoformat()
            }), 201
        else:
            return jsonify({'error': 'Failed to mark attendance'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@attendance_bp.route('/get', methods=['GET'])
def get_attendance():
    """Get attendance records with optional filtering."""
    try:
        user_id = request.args.get('user_id', type=int)
        date_str = request.args.get('date')
        
        # Parse date if provided
        target_date = None
        if date_str:
            try:
                target_date = datetime.fromisoformat(date_str)
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
        
        # Get attendance records
        records = tracker.get_attendance(user_id=user_id, date=target_date)
        
        return jsonify({
            'records': records,
            'count': len(records)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@attendance_bp.route('/summary/<int:user_id>', methods=['GET'])
def get_attendance_summary(user_id):
    """Get attendance summary for a user within a date range."""
    try:
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not start_date_str or not end_date_str:
            return jsonify({'error': 'Start date and end date are required'}), 400
        
        try:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        
        if start_date > end_date:
            return jsonify({'error': 'Start date must be before end date'}), 400
        
        # Get attendance summary
        summary = tracker.get_attendance_summary(user_id, start_date, end_date)
        
        return jsonify({
            'user_id': user_id,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'summary': summary
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@attendance_bp.route('/today', methods=['GET'])
def get_today_attendance():
    """Get attendance records for today."""
    try:
        today = datetime.now()
        records = tracker.get_attendance(date=today)
        
        return jsonify({
            'date': today.date().isoformat(),
            'records': records,
            'count': len(records)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@attendance_bp.route('/user/<int:user_id>/today', methods=['GET'])
def get_user_today_attendance(user_id):
    """Get today's attendance record for a specific user."""
    try:
        today = datetime.now()
        records = tracker.get_attendance(user_id=user_id, date=today)
        
        return jsonify({
            'user_id': user_id,
            'date': today.date().isoformat(),
            'records': records,
            'count': len(records)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500