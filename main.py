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
    """Save doctor's notes to Excel"""
    try:
        data = request.get_json()
        patient_name = data.get('patient_name', 'Unknown')
        notes = data.get('notes', '')
        
        excel_writer.save_doctor_notes(patient_name, notes)
        return jsonify({'success': True, 'message': 'Notes saved successfully'})
    except Exception as e:
        logging.error(f"Error saving notes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/save_test_result', methods=['POST'])
def save_test_result():
    """Save test results from individual test modules"""
    try:
        logging.info("Received save_test_result request")
        data = request.get_json()
        
        if not data:
            logging.error("No JSON data received")
            return jsonify({'success': False, 'message': 'No data received'}), 400
            
        test_name = data.get('test_name', 'unknown')
        patient_name = data.get('patient_name', 'Unknown')
        
        logging.info(f"Saving test result for {test_name} - Patient: {patient_name}")
        logging.debug(f"Test data: {data}")
        
        # Save to Excel
        excel_writer.save_test_result(test_name, patient_name, data)
        
        response = {'success': True, 'message': 'Test result saved successfully'}
        logging.info("Test result saved successfully")
        return jsonify(response)
        
    except Exception as e:
        logging.error(f"Error saving test result: {e}")
        import traceback
        logging.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': str(e)}), 500

# WebSocket events for real-time communication
@socketio.on('join_doctor')
def on_join_doctor():
    join_room(doctor_room)
    emit('status', {'msg': 'Doctor connected'})
    logging.info("Doctor joined the room")

@socketio.on('join_patient')
def on_join_patient():
    join_room(patient_room)
    emit('status', {'msg': 'Patient connected'})
    # Notify doctor that patient is online
    socketio.emit('patient_status', {'online': True}, to=doctor_room)
    logging.info("Patient joined the room")

@socketio.on('disconnect')
def on_disconnect():
    # Notify doctor if patient disconnects
    socketio.emit('patient_status', {'online': False}, to=doctor_room)
    logging.info("Client disconnected")

@socketio.on('doctor_command')
def handle_doctor_command(data):
    """Handle commands from doctor to patient"""
    command = data.get('command')
    test_name = data.get('test', '')
    
    logging.info(f"Doctor command: {command} for test: {test_name}")
    
    # Send command to patient
    socketio.emit('doctor_instruction', {
        'command': command,
        'test': test_name
    }, to=patient_room)
    
    # Confirm to doctor
    emit('command_sent', {'command': command, 'test': test_name})

@socketio.on('test_completed')
def handle_test_completion(data):
    """Handle test completion from patient"""
    logging.info(f"Test completed: {data}")
    
    # Add timestamp if not present
    if 'timestamp' not in data:
        data['timestamp'] = int(time.time() * 1000)
    
    # Notify doctor about test completion
    socketio.emit('test_result', data, to=doctor_room)
    
    # Also send as patient view update for real-time monitoring
    socketio.emit('patient_view_update', {
        'action': 'test_completed',
        'test': data.get('test_name', 'unknown'),
        'patient': data.get('patient_name', 'unknown'),
        'accuracy': data.get('accuracy', 0),
        'timestamp': data['timestamp']
    }, to=doctor_room)

@socketio.on('patient_view_update')
def handle_patient_view_update(data):
    """Handle patient view updates for doctor synchronization"""
    logging.info(f"Patient view update: {data}")
    
    # Forward to doctor room with enhanced data
    enhanced_data = {
        **data,
        'timestamp': data.get('timestamp', int(time.time() * 1000)),
        'mirror_enabled': True
    }
    
    socketio.emit('patient_view_update', enhanced_data, to=doctor_room)

@socketio.on('enable_screen_mirror')
def handle_screen_mirror(data):
    """Handle screen mirroring requests from doctor"""
    socketio.emit('mirror_screen', data, to=patient_room)

@socketio.on('patient_screen_data')
def handle_patient_screen_data(data):
    """Handle patient screen data for doctor mirroring"""
    socketio.emit('patient_screen_mirror', data, to=doctor_room)

@socketio.on('patient_navigation')
def handle_patient_navigation(data):
    """Handle patient navigation for doctor monitoring"""
    logging.info(f"Patient navigation: {data}")
    
    # Forward to doctor room
    socketio.emit('patient_navigation', data, to=doctor_room)

@socketio.on('patient_identified')
def handle_patient_identified(data):
    """Handle patient identification"""
    logging.info(f"Patient identified: {data}")
    
    # Forward to doctor room
    socketio.emit('patient_identified', data, to=doctor_room)

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
    
    # Use Flask development server for better compatibility
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
