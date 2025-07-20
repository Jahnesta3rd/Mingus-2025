from flask import Flask, jsonify, request
import sys
import os
import traceback
from dotenv import load_dotenv

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

# Now we can import our module
from src.utils.cashflow_calculator import calculate_daily_cashflow

# Load environment variables
load_dotenv()

app = Flask(__name__)

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route('/forecast', methods=['POST'])
def generate_forecast():
    """Generate cashflow forecast for a user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'user_id' not in data or 'initial_balance' not in data:
            return jsonify({
                "error": "Missing required fields. Please provide user_id and initial_balance"
            }), 400
        
        # Extract parameters
        user_id = data['user_id']
        initial_balance = float(data['initial_balance'])
        start_date = data.get('start_date')  # Optional parameter
        
        # Generate forecast
        forecast_results = calculate_daily_cashflow(
            user_id=user_id,
            initial_balance=initial_balance,
            start_date=start_date
        )
        
        return jsonify({
            "status": "success",
            "data": forecast_results
        }), 200
        
    except ValueError as ve:
        print(f"ValueError: {str(ve)}")
        return jsonify({
            "error": "Invalid input data",
            "details": str(ve)
        }), 400
        
    except Exception as e:
        # Print the full error traceback
        print("Error in generate_forecast:")
        print(traceback.format_exc())
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    # Print environment check
    print("\nEnvironment variables:")
    print(f"SUPABASE_URL: {'Set' if os.getenv('SUPABASE_URL') else 'Not set'}")
    print(f"SUPABASE_ANON_KEY: {'Set' if os.getenv('SUPABASE_ANON_KEY') else 'Not set'}")
    print(f"PORT: {port}")
    print(f"FLASK_ENV: {os.getenv('FLASK_ENV')}\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug) 