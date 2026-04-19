#!/usr/bin/env python3
"""
Tommy's Skips - SIMPLE STABLE VERSION
No auto-reload, no file watching, just works
"""

from flask import Flask, render_template_string, request, redirect, url_for, jsonify
import sqlite3
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'tommys_skips_stable'

def init_db():
    """Initialize database"""
    conn = sqlite3.connect('tommys_skips_stable.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            customer_email TEXT,
            address TEXT NOT NULL,
            postcode TEXT NOT NULL,
            skip_size TEXT NOT NULL,
            job_type TEXT NOT NULL,
            job_date TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            assigned_to TEXT NOT NULL,
            payment_method TEXT DEFAULT 'Unpaid',
            amount REAL,
            vat_amount REAL,
            total_amount REAL,
            status TEXT DEFAULT 'Booked',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Fleet tracking
    c.execute('''
        CREATE TABLE IF NOT EXISTS skip_fleet (
            size TEXT PRIMARY KEY,
            total_owned INTEGER DEFAULT 10
        )
    ''')
    
    # Insert default fleet
    sizes = ['Mini 4yd', 'Midi 6yd', 'Maxi 8yd']
    for size in sizes:
        c.execute('INSERT OR IGNORE INTO skip_fleet (size) VALUES (?)', (size,))
    
    conn.commit()
    conn.close()

def get_inventory():
    """Get current inventory status"""
    conn = sqlite3.connect('tommys_skips_stable.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get fleet totals
    c.execute('SELECT * FROM skip_fleet')
    fleet = {row['size']: row['total_owned'] for row in c.fetchall()}
    
    # Count skips out
    c.execute('''
        SELECT skip_size, COUNT(*) as out_count
        FROM orders 
        WHERE status IN ('Delivered', 'Booked')
        GROUP BY skip_size
    ''')
    out_counts = {row['skip_size']: row['out_count'] for row in c.fetchall()}
    
    # Calculate totals
    inventory = {}
    total_owned = total_out = total_available = 0
    
    for size, owned in fleet.items():
        out = out_counts.get(size, 0)
        available = owned - out
        inventory[size] = {
            'owned': owned, 'out': out, 'available': available,
            'utilization': round((out/owned*100) if owned > 0 else 0, 1)
        }
        total_owned += owned
        total_out += out
        total_available += available
    
    conn.close()
    return {
        'by_size': inventory,
        'totals': {'owned': total_owned, 'out': total_out, 'available': total_available,
                  'utilization': round((total_out/total_owned*100) if total_owned > 0 else 0, 1)}
    }

@app.route('/')
def dashboard():
    """Dashboard with inventory"""
    inventory = get_inventory()
    
    inventory_html = f'''
    <div class="inventory-panel">
        <h2>📦 Skip Inventory</h2>
        <div class="totals">
            <div class="total-item">
                <div class="number">{inventory['totals']['owned']}</div>
                <div class="label">Total Fleet</div>
            </div>
            <div class="total-item out">
                <div class="number">{inventory['totals']['out']}</div>
                <div class="label">Out with Customers</div>
            </div>
            <div class="total-item available">
                <div class="number">{inventory['totals']['available']}</div>
                <div class="label">Available</div>
            </div>
            <div class="total-item">
                <div class="number">{inventory['totals']['utilization']}%</div>
                <div class="label">Utilization</div>
            </div>
        </div>
        
        <div class="by-size">
    '''
    
    for size, data in inventory['by_size'].items():
        status = "low-stock" if data['utilization'] >= 80 else ""
        inventory_html += f'''
            <div class="size-row {status}">
                <span class="size-name">{size}</span>
                <span>{data['owned']} owned | {data['out']} out | {data['available']} available ({data['utilization']}%)</span>
            </div>
        '''
    
    inventory_html += '</div></div>'
    
    return render_template_string(DASHBOARD_TEMPLATE.format(inventory=inventory_html))

@app.route('/new', methods=['GET', 'POST'])
def new_order():
    """New order form"""
    if request.method == 'POST':
        try:
            # Get all form data
            customer_name = request.form.get('customer_name', '').strip()
            customer_phone = request.form.get('customer_phone', '').strip()
            customer_email = request.form.get('customer_email', '').strip()
            address = request.form.get('address', '').strip()
            postcode = request.form.get('postcode', '').strip()
            skip_size = request.form.get('skip_size', '').strip()
            job_type = request.form.get('job_type', '').strip()
            job_date = request.form.get('job_date', '').strip()
            time_slot = request.form.get('time_slot', '').strip()
            assigned_to = request.form.get('assigned_to', '').strip()
            payment_method = request.form.get('payment_method', 'Unpaid')
            
            # Validate required fields
            required_fields = {
                'customer_name': customer_name,
                'customer_phone': customer_phone,
                'address': address,
                'postcode': postcode,
                'skip_size': skip_size,
                'job_type': job_type,
                'job_date': job_date,
                'time_slot': time_slot,
                'assigned_to': assigned_to
            }
            
            missing_fields = [field for field, value in required_fields.items() if not value]
            
            if missing_fields:
                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                print(f"Form validation error: {error_msg}")
                print(f"Received data: {dict(request.form)}")
                return render_template_string(NEW_ORDER_TEMPLATE, error=error_msg)
            
            # Calculate pricing
            pricing = {'Mini 4yd': 120.00, 'Midi 6yd': 170.00, 'Maxi 8yd': 220.00}
            total = pricing.get(skip_size, 120.00)
            vat = total * 0.2
            net = total - vat
            
            # Save to database
            conn = sqlite3.connect('tommys_skips_stable.db')
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO orders 
                (customer_name, customer_phone, customer_email, address, postcode,
                 skip_size, job_type, job_date, time_slot, assigned_to, payment_method,
                 amount, vat_amount, total_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (customer_name, customer_phone, customer_email, address, postcode,
                  skip_size, job_type, job_date, time_slot, assigned_to, payment_method,
                  net, vat, total))
            
            conn.commit()
            conn.close()
            
            print(f"Order saved successfully: {customer_name} - {skip_size}")
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            error_msg = f"Error saving order: {str(e)}"
            print(f"Database error: {error_msg}")
            return render_template_string(NEW_ORDER_TEMPLATE, error=error_msg)
    
    # GET request - show form
    tomorrow = datetime.now() + timedelta(days=1)
    default_date = tomorrow.strftime('%Y-%m-%d')
    return render_template_string(NEW_ORDER_TEMPLATE, default_date=default_date)

@app.route('/orders')
def orders():
    """View all orders"""
    conn = sqlite3.connect('tommys_skips_stable.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM orders ORDER BY created_at DESC')
    orders = c.fetchall()
    conn.close()
    
    orders_html = ""
    for order in orders:
        orders_html += f'''
        <div class="order-card">
            <h3>{order['customer_name']} - {order['skip_size']}</h3>
            <p>📍 {order['address']}, {order['postcode']}</p>
            <p>📞 {order['customer_phone']} | 📅 {order['job_date']} ({order['time_slot']})</p>
            <p>👤 {order['assigned_to']} | 💰 £{order['total_amount']:.2f} | Status: {order['status']}</p>
        </div>
        '''
    
    return render_template_string(ORDERS_TEMPLATE.format(orders=orders_html))

@app.route('/api/status')
def api_status():
    """API endpoint for real-time status updates"""
    inventory = get_inventory()
    
    conn = sqlite3.connect('tommys_skips_stable.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM orders WHERE DATE(created_at) = DATE("now")')
    today_orders = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM orders')
    total_orders = c.fetchone()[0]
    conn.close()
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'inventory': inventory,
        'orders': {
            'today': today_orders,
            'total': total_orders
        }
    })

# Templates
DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Tommy's Skips Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="30">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: Arial, sans-serif; background: #1a1a1a; color: white; }}
        .header {{ background: #2c5aa0; padding: 1rem; text-align: center; }}
        .container {{ padding: 2rem; max-width: 1200px; margin: 0 auto; }}
        .big-button {{ 
            background: #ff6b35; color: white; padding: 2rem; border: none; 
            border-radius: 15px; font-size: 1.5rem; cursor: pointer; 
            width: 100%; margin: 1rem 0; text-decoration: none;
            display: block; text-align: center;
        }}
        .big-button:hover {{ background: #e55a2b; }}
        .inventory-panel {{ background: #2a2a2a; padding: 1.5rem; border-radius: 15px; margin: 1rem 0; }}
        .inventory-panel h2 {{ color: #ff6b35; margin-bottom: 1rem; text-align: center; }}
        .totals {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }}
        .total-item {{ background: #333; padding: 1rem; border-radius: 8px; text-align: center; }}
        .total-item.out {{ border-left: 4px solid #ff4444; }}
        .total-item.available {{ border-left: 4px solid #44ff44; }}
        .total-item .number {{ font-size: 2rem; font-weight: bold; color: #ff6b35; }}
        .total-item .label {{ color: #ccc; font-size: 0.9rem; }}
        .size-row {{ background: #333; padding: 1rem; margin: 0.5rem 0; border-radius: 8px; display: flex; justify-content: space-between; }}
        .size-row.low-stock {{ border-left: 4px solid #ff4444; background: #4a2c2c; }}
        .size-name {{ font-weight: bold; color: #ff6b35; }}
        .live-indicator {{ 
            background: #2c4a2c; padding: 0.5rem; border-radius: 5px; margin: 1rem 0; 
            text-align: center; color: #44ff44; border: 1px solid #44ff44;
        }}
        .refresh-btn {{ background: #4285F4 !important; }}
        .refresh-btn:hover {{ background: #357ae8 !important; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚛 Tommy's Skips</h1>
        <p>Speed & Reliability You Can Trust</p>
    </div>
    
    <div class="container">
        {inventory}
        
        <div class="live-indicator">🔄 Auto-refreshing every 30 seconds | Last updated: <span id="timestamp"></span></div>
        
        <a href="/new" class="big-button">➕ ADD NEW ORDER</a>
        <a href="/orders" class="big-button">📋 VIEW ALL ORDERS</a>
        <a href="/refresh" class="big-button refresh-btn" onclick="window.location.reload(); return false;">🔄 REFRESH NOW</a>
    </div>
    
    <script>
        // Update timestamp
        document.getElementById('timestamp').textContent = new Date().toLocaleString();
        
        // Visual refresh countdown
        let seconds = 30;
        setInterval(() => {
            seconds--;
            if (seconds <= 0) seconds = 30;
            document.title = `Tommy's Skips (${seconds}s)`;
        }, 1000);
    </script>
</body>
</html>
'''

NEW_ORDER_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>New Order - Tommy's Skips</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: Arial, sans-serif; background: #1a1a1a; color: white; padding: 1rem; }}
        .header {{ background: #2c5aa0; padding: 1rem; text-align: center; margin-bottom: 1rem; border-radius: 8px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #2a2a2a; padding: 2rem; border-radius: 8px; }}
        .form-row {{ margin-bottom: 1rem; }}
        label {{ display: block; margin-bottom: 0.5rem; font-weight: bold; color: #ff6b35; }}
        input, select {{ width: 100%; padding: 0.75rem; border: 1px solid #555; border-radius: 5px; background: #333; color: white; font-size: 1rem; }}
        input:focus, select:focus {{ outline: none; border-color: #ff6b35; }}
        .button-group {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; margin-bottom: 1rem; }}
        .btn {{ padding: 1rem; border: 1px solid #555; border-radius: 5px; background: #333; color: white; cursor: pointer; text-align: center; }}
        .btn:hover, .btn.active {{ background: #ff6b35; border-color: #ff6b35; }}
        .submit-btn {{ background: #ff6b35; color: white; padding: 1rem 2rem; border: none; border-radius: 5px; font-size: 1.2rem; cursor: pointer; width: 100%; }}
        .submit-btn:hover {{ background: #e55a2b; }}
        .back-btn {{ background: #666; color: white; padding: 0.5rem 1rem; text-decoration: none; border-radius: 5px; display: inline-block; margin-bottom: 1rem; }}
        .error {{ background: #ff4444; color: white; padding: 1rem; border-radius: 5px; margin-bottom: 1rem; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>➕ Add New Order</h1>
    </div>
    
    <div class="container">
        <a href="/" class="back-btn">← Back to Dashboard</a>
        
        {% if error %}
        <div class="error">❌ {{ error }}</div>
        {% endif %}
        
        <form method="POST">            
            <div class="form-row">
                <label for="customer_name">Customer Name *</label>
                <input type="text" id="customer_name" name="customer_name" required>
            </div>
            
            <div class="form-row">
                <label for="customer_phone">Phone *</label>
                <input type="tel" id="customer_phone" name="customer_phone" required>
            </div>
            
            <div class="form-row">
                <label for="customer_email">Email</label>
                <input type="email" id="customer_email" name="customer_email">
            </div>
            
            <div class="form-row">
                <label for="address">Address *</label>
                <input type="text" id="address" name="address" required>
            </div>
            
            <div class="form-row">
                <label for="postcode">Postcode *</label>
                <input type="text" id="postcode" name="postcode" required>
            </div>
            
            <div class="form-row">
                <label>Skip Size *</label>
                <div class="button-group">
                    <div class="btn skip-option" onclick="selectSkip('Mini 4yd', this)">Mini 4yd<br>£120</div>
                    <div class="btn skip-option" onclick="selectSkip('Midi 6yd', this)">Midi 6yd<br>£170</div>
                    <div class="btn skip-option" onclick="selectSkip('Maxi 8yd', this)">Maxi 8yd<br>£220</div>
                </div>
                <input type="hidden" id="skip_size" name="skip_size" required>
            </div>
            
            <div class="form-row">
                <label>Job Type *</label>
                <div class="button-group">
                    <div class="btn job-option" onclick="selectJob('Deliver', this)">Deliver</div>
                    <div class="btn job-option" onclick="selectJob('Collect', this)">Collect</div>
                    <div class="btn job-option" onclick="selectJob('Swap', this)">Swap</div>
                </div>
                <input type="hidden" id="job_type" name="job_type" required>
            </div>
            
            <div class="form-row">
                <label for="job_date">Job Date *</label>
                <input type="date" id="job_date" name="job_date" value="{{ default_date }}" required>
            </div>
            
            <div class="form-row">
                <label for="time_slot">Time Slot *</label>
                <select id="time_slot" name="time_slot" required>
                    <option value="">Select time slot</option>
                    <option value="Early Morning (7am-9am)">Early Morning (7am-9am)</option>
                    <option value="Morning (9am-12pm)">Morning (9am-12pm)</option>
                    <option value="Afternoon (12pm-3pm)">Afternoon (12pm-3pm)</option>
                    <option value="Late Afternoon (3pm-5pm)">Late Afternoon (3pm-5pm)</option>
                </select>
            </div>
            
            <div class="form-row">
                <label for="assigned_to">Assigned To *</label>
                <select id="assigned_to" name="assigned_to" required>
                    <option value="">Select driver</option>
                    <option value="Rob">Rob</option>
                    <option value="Tommy">Tommy</option>
                    <option value="John">John</option>
                </select>
            </div>
            
            <div class="form-row">
                <label for="payment_method">Payment Method</label>
                <select id="payment_method" name="payment_method">
                    <option value="Unpaid">Unpaid</option>
                    <option value="Cash">Cash</option>
                    <option value="Card">Card</option>
                    <option value="Bank Transfer">Bank Transfer</option>
                </select>
            </div>
            
            <button type="submit" class="submit-btn">💾 SAVE ORDER</button>
        </form>
    </div>
    
    <script>
        function selectSkip(size, element) {{
            document.querySelectorAll('.skip-option').forEach(el => el.classList.remove('active'));
            element.classList.add('active');
            document.getElementById('skip_size').value = size;
        }}
        
        function selectJob(type, element) {{
            document.querySelectorAll('.job-option').forEach(el => el.classList.remove('active'));
            element.classList.add('active');
            document.getElementById('job_type').value = type;
        }}
    </script>
</body>
</html>
'''

ORDERS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>All Orders - Tommy's Skips</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="45">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: Arial, sans-serif; background: #1a1a1a; color: white; }}
        .header {{ background: #2c5aa0; padding: 1rem; text-align: center; }}
        .container {{ padding: 2rem; max-width: 1200px; margin: 0 auto; }}
        .back-btn {{ background: #666; color: white; padding: 0.5rem 1rem; text-decoration: none; border-radius: 5px; display: inline-block; margin-bottom: 1rem; }}
        .order-card {{ background: #333; padding: 1rem; margin: 1rem 0; border-radius: 8px; }}
        .order-card h3 {{ color: #ff6b35; margin-bottom: 0.5rem; }}
        .order-card p {{ margin: 0.25rem 0; color: #ccc; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 All Orders</h1>
    </div>
    
    <div class="container">
        <a href="/" class="back-btn">← Back to Dashboard</a>
        
        <div style="background: #2c4a2c; padding: 0.5rem; border-radius: 5px; margin: 1rem 0; text-align: center; color: #44ff44; border: 1px solid #44ff44;">
            🔄 Auto-refreshing every 45 seconds | Last updated: <span id="orders-timestamp"></span>
        </div>
        
        {orders}
        
        <div style="text-align: center; margin: 2rem 0;">
            <button onclick="window.location.reload()" style="background: #4285F4; color: white; padding: 1rem 2rem; border: none; border-radius: 5px; font-size: 1rem; cursor: pointer;">
                🔄 REFRESH NOW
            </button>
        </div>
    </div>
    
    <script>
        // Update timestamp
        document.getElementById('orders-timestamp').textContent = new Date().toLocaleString();
        
        // Visual refresh countdown
        let seconds = 45;
        setInterval(() => {
            seconds--;
            if (seconds <= 0) seconds = 45;
            document.title = `All Orders (${seconds}s)`;
        }, 1000);
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("Starting Tommy's Skips - STABLE VERSION (no auto-reload)")
    init_db()
    print("Database initialized")
    port = int(os.environ.get('PORT', 8083))
    print(f"Access at: http://localhost:{port}")
    # No debug mode - prevents auto-reloading and file watching
    app.run(host='0.0.0.0', port=port, debug=False)