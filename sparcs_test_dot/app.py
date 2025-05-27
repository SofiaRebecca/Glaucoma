import os
import logging
from flask import Flask, render_template, request, jsonify
import requests

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "sparcs_test_secret")

@app.route('/')
def sparcs_test():
    return render_template('sparcs.html')

@app.route('/api/save_result', methods=['POST'])
def save_result():
    try:
        data = request.get_json()
        
        # Send results to main server
        main_server_url = 'http://localhost:5000/api/save_test_result'
        
        test_data = {
            'test_name': 'sparcs',
            'patient_name': data.get('patient_name', 'Unknown'),
            'duration': data.get('duration', 0),
            'total_points': data.get('total_points', 0),
            'correct_points': data.get('correct_points', 0),
            'quadrant_1': data.get('quadrant_1', 0),
            'quadrant_2': data.get('quadrant_2', 0),
            'quadrant_3': data.get('quadrant_3', 0),
            'quadrant_4': data.get('quadrant_4', 0),
            'start_time': data.get('start_time', ''),
            'end_time': data.get('end_time', ''),
            'responses': data.get('responses', [])
        }
        
        try:
            response = requests.post(main_server_url, json=test_data, timeout=5)
            if response.status_code == 200:
                logging.info("Results saved to main server")
            else:
                logging.warning(f"Failed to save to main server: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logging.warning(f"Could not connect to main server: {e}")
        
        return jsonify({'success': True, 'message': 'Test completed successfully'})
        
    except Exception as e:
        logging.error(f"Error saving result: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8007))
    app.run(host='0.0.0.0', port=port, debug=True)
