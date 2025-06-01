from flask import Flask, render_template_string, request, jsonify
from backend.src.utils.cashflow_calculator_v2 import calculate_daily_cashflow
from datetime import date
import traceback

app = Flask(__name__)

# HTML template with Bootstrap for basic styling
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cashflow Forecast</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { padding: 20px; }
        .result-box { 
            margin-top: 20px; 
            padding: 15px; 
            border-radius: 5px;
            background-color: #f8f9fa;
        }
        .error-message {
            color: #dc3545;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            background-color: #f8d7da;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4">Cashflow Forecast Calculator</h1>
        
        <form method="POST" class="mb-4">
            <div class="mb-3">
                <label for="user_id" class="form-label">User ID:</label>
                <input type="text" class="form-control" id="user_id" name="user_id" required
                       value="{{ request.form.get('user_id', '') }}">
            </div>
            
            <div class="mb-3">
                <label for="initial_balance" class="form-label">Initial Balance:</label>
                <input type="number" step="0.01" class="form-control" id="initial_balance" 
                       name="initial_balance" value="{{ request.form.get('initial_balance', '1000') }}" required>
            </div>
            
            <div class="mb-3">
                <label for="start_date" class="form-label">Start Date:</label>
                <input type="date" class="form-control" id="start_date" name="start_date" 
                       value="{{ request.form.get('start_date', '') }}">
            </div>
            
            <button type="submit" class="btn btn-primary">Calculate Forecast</button>
        </form>

        {% if error %}
        <div class="error-message">
            <h4>Error:</h4>
            <p>{{ error }}</p>
            {% if debug_info %}
            <pre>{{ debug_info }}</pre>
            {% endif %}
        </div>
        {% endif %}

        {% if results %}
        <div class="result-box">
            <h3>Forecast Results</h3>
            <p>Total days calculated: {{ results|length }}</p>
            
            <h4>First 5 days:</h4>
            {% for day in results[:5] %}
            <div class="mb-3">
                <strong>{{ day.forecast_date }}</strong><br>
                Opening Balance: ${{ "%.2f"|format(day.opening_balance) }}<br>
                Income: ${{ "%.2f"|format(day.income) }}<br>
                Expenses: ${{ "%.2f"|format(day.expenses) }}<br>
                Closing Balance: ${{ "%.2f"|format(day.closing_balance) }}<br>
                Status: <span class="badge bg-{{ 'success' if day.balance_status == 'healthy' 
                    else 'warning' if day.balance_status == 'warning' 
                    else 'danger' }}">{{ day.balance_status }}</span>
            </div>
            {% endfor %}
            
            <h4>Last 5 days:</h4>
            {% for day in results[-5:] %}
            <div class="mb-3">
                <strong>{{ day.forecast_date }}</strong><br>
                Opening Balance: ${{ "%.2f"|format(day.opening_balance) }}<br>
                Income: ${{ "%.2f"|format(day.income) }}<br>
                Expenses: ${{ "%.2f"|format(day.expenses) }}<br>
                Closing Balance: ${{ "%.2f"|format(day.closing_balance) }}<br>
                Status: <span class="badge bg-{{ 'success' if day.balance_status == 'healthy' 
                    else 'warning' if day.balance_status == 'warning' 
                    else 'danger' }}">{{ day.balance_status }}</span>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    debug_info = None
    results = None
    
    if request.method == 'POST':
        try:
            # Get form data
            user_id = request.form.get('user_id')
            initial_balance = float(request.form.get('initial_balance', 1000))
            start_date = request.form.get('start_date') or None
            
            # Validate inputs
            if not user_id:
                raise ValueError("User ID is required")
            
            if initial_balance < 0:
                raise ValueError("Initial balance cannot be negative")
            
            # Calculate forecast
            results = calculate_daily_cashflow(
                user_id=user_id,
                initial_balance=initial_balance,
                start_date=start_date
            )
            
        except ValueError as ve:
            error = str(ve)
        except Exception as e:
            error = "An unexpected error occurred while calculating the forecast."
            debug_info = traceback.format_exc()
            print(f"Error in forecast calculation: {str(e)}")
            print(traceback.format_exc())
    
    return render_template_string(
        HTML_TEMPLATE,
        error=error,
        debug_info=debug_info,
        results=results
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True) 