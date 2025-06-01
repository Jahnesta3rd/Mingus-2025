from flask import Flask, request, jsonify
from backend.src.utils.cashflow_calculator_v2 import calculate_daily_cashflow
from flask_cors import CORS
from config import config

app = Flask(__name__)
CORS(app)

# Get configuration based on environment
env = 'development'  # Hardcode to development for now
current_config = config.get(env, config['default'])()

# Print configuration for debugging
print("\nConfiguration Debug:")
print(f"Environment: {env}")
print(f"Supabase URL: {current_config.SUPABASE_URL}")
print(f"Supabase Anon Key: {current_config.SUPABASE_ANON_KEY[:10]}...")
print(f"Port: {current_config.PORT}\n")

@app.route('/api/cashflow/calculate', methods=['POST'])
def calculate_cashflow():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        initial_balance = float(data.get('initial_balance', 0))
        start_date = data.get('start_date')  # Optional

        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400

        try:
            cashflow = calculate_daily_cashflow(user_id, initial_balance, start_date)
            return jsonify(cashflow)
        except Exception as calc_error:
            print(f"\nError in calculate_daily_cashflow:")
            print(f"Error type: {type(calc_error)}")
            print(f"Error message: {str(calc_error)}")
            print(f"Error details: {repr(calc_error)}")
            raise calc_error

    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"\nAPI Error:")
        print(f"Type: {error_type}")
        print(f"Message: {error_msg}")
        print(f"Details: {repr(e)}")
        return jsonify({
            'error': error_msg,
            'error_type': error_type
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=current_config.PORT, debug=True)