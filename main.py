import os
import logging
import threading
import subprocess
import time
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from excel_writer import ExcelWriter

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "glaucoma_detection_secret_key")
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Excel writer
excel_writer = ExcelWriter()

# Global state for doctor-patient communication
doctor_room = "doctor_room"
patient_room = "patient_room"

@app.route('/')
def index():
    """Main entry point - view selector"""
    return render_template('index.html')

@app.route('/doctor')
def doctor_view():
    """Doctor dashboard with patient supervision"""
    return render_template('doctor.html')

@app.route('/patient')
def patient_view():
    """Patient interface for test selection"""
    return render_template('patient.html')

@app.route('/api/save_notes', methods=['POST'])
def save_notes():
    """Save doctor's notes"""
    try:
        data = request.get_json()
        patient_name = data.get('patient_name', 'Unknown')
        notes_data = {
            'symptoms': data.get('symptoms', ''),
            'medical_concerns': data.get('medical_concerns', ''),
            'additional_notes': data.get('additional_notes', '')
        }

        excel_writer.save_doctor_notes(patient_name, notes_data)
        return jsonify({'status': 'success'})
    except Exception as e:
        logging.error(f"Error saving notes: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/save_result', methods=['POST'])
def save_result():
    """Save test results"""
    try:
        data = request.get_json()

        # Extract test information
        test_name = data.get('test_name', 'visual_field')
        patient_name = data.get('patient', {}).get('name', 'Unknown')

        # Prepare test data for Excel
        test_data = {
            'start_time': data.get('startTime', ''),
            'end_time': data.get('endTime', ''),
            'duration': data.get('duration', 0),
            'total_points': len(data.get('testResults', [])),
            'correct_points': len([r for r in data.get('testResults', []) if r.get('seen', False)]),
            'points_tested': len(data.get('testResults', [])),
            'sensitivity_map': data.get('thresholds', []),
            'defects_detected': len([t for t in data.get('thresholds', []) if t < 20]),
            'false_positives': data.get('falsePositives', 0),
            'false_negatives': data.get('falseNegatives', 0),
            'fixation_losses': data.get('fixationLosses', 0),
            'reliability_trials': data.get('reliabilityTrials', 0),
            'doctor_notes': data.get('doctor_notes', '')
        }

        excel_writer.save_test_result(test_name, patient_name, test_data)
        return jsonify({'status': 'success'})
    except Exception as e:
        logging.error(f"Error saving test result: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# SocketIO event handlers for doctor-patient communication
@socketio.on('join_doctor')
def handle_join_doctor():
    """Doctor joins monitoring room"""
    join_room(doctor_room)
    emit('status', {'message': 'Connected to doctor monitoring'})

@socketio.on('join_patient')
def handle_join_patient():
    """Patient joins test room"""
    join_room(patient_room)
    emit('status', {'message': 'Connected to patient interface'})

@socketio.on('patient_mouse_move')
def handle_patient_mouse_move(data):
    """Handle patient mouse movement for mirroring"""
    socketio.emit('patient_mouse_data', data, to=doctor_room)

@socketio.on('patient_click')
def handle_patient_click(data):
    """Handle patient clicks for mirroring"""
    socketio.emit('patient_click_data', data, to=doctor_room)

@socketio.on('patient_keyboard')
def handle_patient_keyboard(data):
    """Handle patient keyboard events for mirroring"""
    socketio.emit('patient_keyboard_data', data, to=patient_room)

@socketio.on('doctor_remote_click')
def handle_doctor_remote_click(data):
    """Handle doctor remote clicks on patient screen"""
    socketio.emit('remote_click_command', data, to=patient_room)

@socketio.on('doctor_remote_scroll')
def handle_doctor_remote_scroll(data):
    """Handle doctor remote scroll on patient screen"""
    socketio.emit('remote_scroll_command', data, to=patient_room)

@socketio.on('start_screen_mirror')
def handle_start_screen_mirror(data):
    """Start screen mirroring session"""
    socketio.emit('begin_screen_capture', data, to=patient_room)
    socketio.emit('mirror_session_started', data, to=doctor_room)

@socketio.on('stop_screen_mirror')
def handle_stop_screen_mirror(data):
    """Stop screen mirroring session"""
    socketio.emit('stop_screen_capture', data, to=patient_room)
    socketio.emit('mirror_session_stopped', data, to=doctor_room)

# Visual Field Test specific events
@socketio.on('test_started')
def handle_test_started(data):
    """Handle test start notification"""
    socketio.emit('test_status', {
        'status': 'started',
        'patient': data.get('patient'),
        'testType': data.get('testType')
    }, to=doctor_room)

@socketio.on('stimulus_presented')
def handle_stimulus_presented(data):
    """Handle stimulus presentation notification"""
    socketio.emit('stimulus_update', {
        'pointIndex': data.get('pointIndex'),
        'intensity': data.get('intensity'),
        'position': data.get('position')
    }, to=doctor_room)

@socketio.on('response_recorded')
def handle_response_recorded(data):
    """Handle patient response notification"""
    socketio.emit('response_update', {
        'pointIndex': data.get('pointIndex'),
        'seen': data.get('seen'),
        'responseTime': data.get('responseTime'),
        'currentThreshold': data.get('currentThreshold')
    }, to=doctor_room)

@socketio.on('test_completed')
def handle_test_completed(data):
    """Handle test completion notification"""
    socketio.emit('test_finished', {
        'status': 'completed',
        'results': data
    }, to=doctor_room)

# Add test routes to serve tests directly from main app
@app.route('/test/<test_name>')
def run_test(test_name):
    """Serve tests directly from main app"""
    # Map test names to template files
    test_templates = {
        'visual_field': 'visual_field.html',
        'csv1000': 'csv1000.html',
        'edge': 'edge.html',
        'motion': 'motion.html',
        'pattern': 'pattern.html',
        'pelli_robinson': 'pelli_robinson.html',
        'sparcs': 'sparcs.html'
    }

    template = test_templates.get(test_name)
    if template:
        return render_template(template)
    else:
        return redirect(url_for('patient_view'))

if __name__ == '__main__':
    # Start main application on port 5000 for Replit compatibility
    logging.info("Starting Glaucoma Detection System on port 5000...")

    # Use SocketIO run for better mobile compatibility and WebSocket support
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)