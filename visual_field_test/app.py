
import os
import logging
from flask import Flask, render_template, request, jsonify
import requests

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "visual_field_secret")

@app.route('/')
def visual_field_test():
    return render_template('visual_field.html')

@app.route('/api/save_result', methods=['POST'])
def save_result():
    try:
        data = request.get_json()
        
        # Send results to main server
        main_server_url = 'http://localhost:5000/api/save_test_result'
        
        # Format data for main server
        test_data = {
            'test_name': 'humphrey_visual_field_24_2',
            'patient_name': data.get('patient_name', 'Unknown'),
            'patient_age': data.get('patient_age', 'Unknown'),
            'patient_id': data.get('patient_id', 'Unknown'),
            'duration': data.get('duration', 0),
            'total_points': data.get('total_points', 54),
            'correct_points': data.get('points_seen', 0),
            'detection_rate': data.get('detection_rate', 0),
            'mean_deviation': data.get('mean_deviation', 0),
            'pattern_standard_deviation': data.get('pattern_standard_deviation', 0),
            'visual_field_index': data.get('visual_field_index', 0),
            'false_positives': data.get('false_positives', 0),
            'false_negatives': data.get('false_negatives', 0),
            'fixation_losses': data.get('fixation_losses', 0),
            'reliability_score': data.get('reliability_score', 'Good'),
            'threshold_map': data.get('threshold_map', []),
            'responses': data.get('responses', []),
            'start_time': data.get('start_time', ''),
            'end_time': data.get('end_time', '')
        }
        
        try:
            response = requests.post(main_server_url, json=test_data, timeout=5)
            if response.status_code == 200:
                logging.info("Visual field test results saved to main server")
            else:
                logging.warning(f"Failed to save to main server: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logging.warning(f"Could not connect to main server: {e}")
        
        return jsonify({'success': True, 'message': 'Humphrey Visual Field test completed successfully'})
        
    except Exception as e:
        logging.error(f"Error saving visual field result: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8001))
    app.run(host='0.0.0.0', port=port, debug=False)
