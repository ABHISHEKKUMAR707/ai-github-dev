from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, date
from attendance import AttendanceTracker

app = Flask(__name__)
tracker = AttendanceTracker()

@app.route('/')
def index():
    """Home page with navigation to attendance features"""
    return render_template('index.html')

@app.route('/attendance')
def attendance_page():
    """Main attendance tracking page"""
    today = date.today().strftime("%Y-%m-%d")
    today_attendance = tracker.get_attendance(date_filter=today)
    return render_template('attendance.html', today_attendance=today_attendance, today=today)

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    """API endpoint to mark attendance"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        status = data.get('status', 'present')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        success = tracker.mark_attendance(user_id, status)
        
        if success:
            return jsonify({
                'success': True, 
                'message': f'Attendance marked for {user_id} as {status}'
            })
        else:
            return jsonify({'error': 'Failed to mark attendance'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_attendance')
def get_attendance():
    """API endpoint to get attendance records"""
    user_id = request.args.get('user_id')
    date_filter = request.args.get('date')
    
    try:
        records = tracker.get_attendance(user_id=user_id, date_filter=date_filter)
        
        # Convert datetime objects to strings for JSON serialization
        serialized_records = []
        for record in records:
            serialized_record = record.copy()
            serialized_record['timestamp'] = record['timestamp'].isoformat()
            serialized_records.append(serialized_record)
        
        return jsonify({'records': serialized_records})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/attendance_summary')
def attendance_summary():
    """API endpoint to get attendance summary"""
    user_id = request.args.get('user_id')
    
    try:
        summary = tracker.get_attendance_summary(user_id=user_id)
        return jsonify(summary)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/users_present_today')
def users_present_today():
    """API endpoint to get users present today"""
    try:
        users = tracker.get_users_present_today()
        return jsonify({'users': users})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/check_attendance/<user_id>')
def check_user_attendance(user_id):
    """API endpoint to check if a specific user is present today"""
    try:
        is_present = tracker.is_user_present_today(user_id)
        return jsonify({
            'user_id': user_id,
            'present_today': is_present
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reports')
def reports_page():
    """Attendance reports page"""
    all_records = tracker.get_attendance()
    overall_summary = tracker.get_attendance_summary()
    return render_template('reports.html', records=all_records, summary=overall_summary)

if __name__ == '__main__':
    app.run(debug=True)