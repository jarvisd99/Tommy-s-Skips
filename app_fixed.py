#!/usr/bin/env python3
"""
Tommy's Skips - FIXED VERSION
Skip hire management with working forms
"""

from flask import Flask, render_template_string, request, redirect, url_for, jsonify, session
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
import os

# Import route optimizer if available
try:
    from route_optimizer import TommysRouteOptimizer
    ROUTES_ENABLED = True
except ImportError:
    ROUTES_ENABLED = False

# Import inventory tracker
try:
    from inventory_tracker import SkipInventory
    INVENTORY_ENABLED = True
except ImportError:
    INVENTORY_ENABLED = False

app = Flask(__name__)
app.secret_key = 'tommys_skips_secret_key_2024'

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('tommys_skips.db')
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
    
    conn.commit()
    conn.close()

@app.route('/')
def dashboard():
    """Main dashboard with inventory tracking"""
    
    # Get inventory status
    inventory_html = ""
    if INVENTORY_ENABLED:
        tracker = SkipInventory()
        status = tracker.get_detailed_status()
        inventory = status['inventory']
        alerts = status['alerts']
        
        # Build inventory display
        inventory_html = f'''
        <div class="inventory-panel">
            <h2>📦 Skip Inventory Status</h2>
            <div class="totals">
                <div class="total-item">
                    <div class="number">{inventory['totals']['total_owned']}</div>
                    <div class="label">Total Fleet</div>
                </div>
                <div class="total-item out">
                    <div class="number">{inventory['totals']['total_out']}</div>
                    <div class="label">Out with Customers</div>
                </div>
                <div class="total-item available">
                    <div class="number">{inventory['totals']['total_available']}</div>
                    <div class="label">Available in Depot</div>
                </div>
                <div class="total-item utilization">
                    <div class="number">{inventory['totals']['utilization_percent']}%</div>
                    <div class="label">Utilization Rate</div>
                </div>
            </div>
            
            <div class="by-size">
                <h3>By Skip Size:</h3>
        '''
        
        for size, data in inventory['by_size'].items():
            status_class = "low-stock" if data['utilization_percent'] >= 80 else ""
            inventory_html += f'''
                <div class="size-row {status_class}">
                    <div class="size-name">{size}</div>
                    <div class="size-stats">
                        <span>📦 {data['total_owned']} owned</span>
                        <span>📤 {data['out_with_customers']} out</span>
                        <span>🏠 {data['available_in_depot']} available</span>
                        <span>📊 {data['utilization_percent']}%</span>
                    </div>
                </div>
            '''
        
        inventory_html += "</div>"
        
        # Add alerts if any
        if alerts:
            inventory_html += '<div class="alerts"><h3>⚠️ Low Stock Alerts:</h3>'
            for alert in alerts:
                inventory_html += f'<div class="alert">{alert["message"]}</div>'
            inventory_html += '</div>'
        
        inventory_html += '</div>'
    
    return render_template_string(f'''
<!DOCTYPE html>
<html>
<head>
    <title>Tommy's Skips - Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #1a1a1a; color: white; }
        .header { background: #2c5aa0; padding: 1rem; text-align: center; }
        .container { padding: 2rem; max-width: 1200px; margin: 0 auto; }
        .big-button { 
            background: #ff6b35; 
            color: white; 
            padding: 2rem; 
            border: none; 
            border-radius: 15px; 
            font-size: 1.5rem; 
            cursor: pointer; 
            width: 100%; 
            margin: 1rem 0; 
            text-decoration: none;
            display: block;
            text-align: center;
        }
        .big-button:hover { background: #e55a2b; }
        
        .inventory-panel { 
            background: #2a2a2a; 
            padding: 1.5rem; 
            border-radius: 15px; 
            margin: 1rem 0; 
        }
        .inventory-panel h2 { 
            color: #ff6b35; 
            margin-bottom: 1rem; 
            text-align: center;
        }
        .totals { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
            gap: 1rem; 
            margin-bottom: 1.5rem;
        }
        .total-item { 
            background: #333; 
            padding: 1rem; 
            border-radius: 8px; 
            text-align: center;
        }
        .total-item.out { border-left: 4px solid #ff4444; }
        .total-item.available { border-left: 4px solid #44ff44; }
        .total-item.utilization { border-left: 4px solid #4444ff; }
        .total-item .number { 
            font-size: 2rem; 
            font-weight: bold; 
            color: #ff6b35;
        }
        .total-item .label { 
            color: #ccc; 
            font-size: 0.9rem;
        }
        .by-size h3 { 
            color: #ff6b35; 
            margin-bottom: 0.5rem;
        }
        .size-row { 
            background: #333; 
            padding: 1rem; 
            margin: 0.5rem 0; 
            border-radius: 8px; 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
        }
        .size-row.low-stock { 
            border-left: 4px solid #ff4444; 
            background: #4a2c2c;
        }
        .size-name { 
            font-weight: bold; 
            color: #ff6b35;
        }
        .size-stats span { 
            margin: 0 0.5rem; 
            font-size: 0.9rem;
        }
        .alerts { 
            margin-top: 1rem; 
            padding: 1rem; 
            background: #4a2c2c; 
            border-radius: 8px; 
            border-left: 4px solid #ff4444;
        }
        .alerts h3 { color: #ff4444; }
        .alert { 
            background: #333; 
            padding: 0.5rem; 
            margin: 0.5rem 0; 
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚛 Tommy's Skips</h1>
        <p>Speed & Reliability You Can Trust</p>
    </div>
    
    <div class="container">
        {inventory_html}
        
        <a href="/new" class="big-button">➕ ADD NEW ORDER</a>
        <a href="/orders" class="big-button">📋 VIEW ALL ORDERS</a>
        <a href="/routes" class="big-button">🗺️ DAILY ROUTES</a>
        <a href="/inventory" class="big-button">📦 MANAGE INVENTORY</a>
    </div>
</body>
</html>
    ''')

@app.route('/new', methods=['GET', 'POST'])
def new_order():
    """Add new order - FIXED VERSION"""
    if request.method == 'POST':
        try:
            # Get form data
            data = {
                'customer_name': request.form['customer_name'],
                'customer_phone': request.form['customer_phone'],
                'customer_email': request.form.get('customer_email', ''),
                'address': request.form['address'],
                'postcode': request.form['postcode'],
                'skip_size': request.form['skip_size'],
                'job_type': request.form['job_type'],
                'job_date': request.form['job_date'],
                'time_slot': request.form['time_slot'],
                'assigned_to': request.form['assigned_to'],
                'payment_method': request.form.get('payment_method', 'Unpaid')
            }
            
            # Calculate pricing
            pricing = {
                'Mini 4yd': 120.00,
                'Midi 6yd': 170.00,
                'Maxi 8yd': 220.00
            }
            
            total = pricing.get(data['skip_size'], 120.00)
            vat = total * 0.2
            net = total - vat
            
            # Save to database
            conn = sqlite3.connect('tommys_skips.db')
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO orders 
                (customer_name, customer_phone, customer_email, address, postcode, 
                 skip_size, job_type, job_date, time_slot, assigned_to, payment_method, 
                 amount, vat_amount, total_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['customer_name'], data['customer_phone'], data['customer_email'],
                data['address'], data['postcode'], data['skip_size'], data['job_type'],
                data['job_date'], data['time_slot'], data['assigned_to'], data['payment_method'],
                net, vat, total
            ))
            
            conn.commit()
            conn.close()
            
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    # GET request - show form
    return render_template_string(NEW_ORDER_TEMPLATE)

@app.route('/orders')
def orders():
    """View all orders"""
    conn = sqlite3.connect('tommys_skips.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT * FROM orders ORDER BY created_at DESC')
    orders = c.fetchall()
    conn.close()
    
    orders_html = ""
    for order in orders:
        orders_html += f'''
        <div style="background: #333; padding: 1rem; margin: 1rem 0; border-radius: 8px;">
            <h3>{order['customer_name']} - {order['skip_size']}</h3>
            <p>📍 {order['address']}, {order['postcode']}</p>
            <p>📞 {order['customer_phone']} | 📅 {order['job_date']} | 👤 {order['assigned_to']}</p>
            <p>💰 £{order['total_amount']:.2f} | Status: {order['status']}</p>
        </div>
        '''
    
    return render_template_string(f'''
<!DOCTYPE html>
<html>
<head>
    <title>All Orders - Tommy's Skips</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: Arial, sans-serif; background: #1a1a1a; color: white; }}
        .header {{ background: #2c5aa0; padding: 1rem; text-align: center; }}
        .container {{ padding: 2rem; max-width: 1200px; margin: 0 auto; }}
        .back-btn {{ background: #666; color: white; padding: 0.5rem 1rem; text-decoration: none; border-radius: 5px; display: inline-block; margin-bottom: 1rem; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 All Orders</h1>
    </div>
    
    <div class="container">
        <a href="/" class="back-btn">← Back to Dashboard</a>
        {orders_html}
    </div>
</body>
</html>
    ''')

@app.route('/routes')
def routes():
    """Daily routes page"""
    if not ROUTES_ENABLED:
        return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Routes - Tommy's Skips</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #1a1a1a; color: white; text-align: center; padding: 2rem; }
    </style>
</head>
<body>
    <h1>🗺️ Routes</h1>
    <p>Route optimizer not available. Install dependencies first.</p>
    <a href="/" style="color: #2c5aa0;">← Back to Dashboard</a>
</body>
</html>
        ''')
    
    # Routes functionality here
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Daily Routes - Tommy's Skips</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #1a1a1a; color: white; text-align: center; padding: 2rem; }
        .back-btn { background: #666; color: white; padding: 0.5rem 1rem; text-decoration: none; border-radius: 5px; display: inline-block; margin-bottom: 1rem; }
    </style>
</head>
<body>
    <h1>🗺️ Daily Routes</h1>
    <a href="/" class="back-btn">← Back to Dashboard</a>
    <p>Route optimization coming soon!</p>
</body>
</html>
    ''')

@app.route('/inventory')
def inventory():
    """Inventory management page"""
    if not INVENTORY_ENABLED:
        return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Inventory - Tommy's Skips</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #1a1a1a; color: white; text-align: center; padding: 2rem; }
    </style>
</head>
<body>
    <h1>📦 Inventory</h1>
    <p>Inventory tracking not available.</p>
    <a href="/" style="color: #2c5aa0;">← Back to Dashboard</a>
</body>
</html>
        ''')
    
    tracker = SkipInventory()
    status = tracker.get_detailed_status()
    
    return render_template_string(INVENTORY_TEMPLATE, status=status)

@app.route('/update-fleet', methods=['POST'])
def update_fleet():
    """Update fleet sizes"""
    if not INVENTORY_ENABLED:
        return jsonify({'error': 'Inventory tracking not available'})
    
    try:
        tracker = SkipInventory()
        
        mini_total = int(request.form.get('mini_total', 10))
        midi_total = int(request.form.get('midi_total', 10))
        maxi_total = int(request.form.get('maxi_total', 10))
        
        tracker.update_fleet_size('Mini 4yd', mini_total)
        tracker.update_fleet_size('Midi 6yd', midi_total)
        tracker.update_fleet_size('Maxi 8yd', maxi_total)
        
        return redirect(url_for('inventory'))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# New Order Form Template (FIXED)
NEW_ORDER_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>New Order - Tommy's Skips</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: Arial, sans-serif; 
            background: #1a1a1a; 
            color: white; 
            padding: 1rem;
        }
        .header { 
            background: #2c5aa0; 
            padding: 1rem; 
            text-align: center; 
            margin-bottom: 1rem; 
            border-radius: 8px;
        }
        .container { 
            max-width: 600px; 
            margin: 0 auto; 
            background: #2a2a2a; 
            padding: 2rem; 
            border-radius: 8px;
        }
        .form-row { margin-bottom: 1rem; }
        label { 
            display: block; 
            margin-bottom: 0.5rem; 
            font-weight: bold; 
            color: #ff6b35;
        }
        input, select, textarea { 
            width: 100%; 
            padding: 0.75rem; 
            border: 1px solid #555; 
            border-radius: 5px; 
            background: #333; 
            color: white; 
            font-size: 1rem;
        }
        input:focus, select:focus { 
            outline: none; 
            border-color: #ff6b35; 
        }
        .button-group { 
            display: grid; 
            grid-template-columns: repeat(3, 1fr); 
            gap: 0.5rem; 
            margin-bottom: 1rem;
        }
        .btn { 
            padding: 1rem; 
            border: 1px solid #555; 
            border-radius: 5px; 
            background: #333; 
            color: white; 
            cursor: pointer; 
            text-align: center;
        }
        .btn:hover, .btn.active { 
            background: #ff6b35; 
            border-color: #ff6b35; 
        }
        .submit-btn { 
            background: #ff6b35; 
            color: white; 
            padding: 1rem 2rem; 
            border: none; 
            border-radius: 5px; 
            font-size: 1.2rem; 
            cursor: pointer; 
            width: 100%;
        }
        .submit-btn:hover { background: #e55a2b; }
        .back-btn { 
            background: #666; 
            color: white; 
            padding: 0.5rem 1rem; 
            text-decoration: none; 
            border-radius: 5px; 
            display: inline-block; 
            margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>➕ Add New Order</h1>
    </div>
    
    <div class="container">
        <a href="/" class="back-btn">← Back to Dashboard</a>
        
        <form method="POST" id="orderForm">
            
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
                    <div class="btn skip-option" data-value="Mini 4yd">Mini 4yd<br>£120</div>
                    <div class="btn skip-option" data-value="Midi 6yd">Midi 6yd<br>£170</div>
                    <div class="btn skip-option" data-value="Maxi 8yd">Maxi 8yd<br>£220</div>
                </div>
                <input type="hidden" id="skip_size" name="skip_size" required>
            </div>
            
            <div class="form-row">
                <label>Job Type *</label>
                <div class="button-group">
                    <div class="btn job-option" data-value="Deliver">Deliver</div>
                    <div class="btn job-option" data-value="Collect">Collect</div>
                    <div class="btn job-option" data-value="Swap">Swap</div>
                </div>
                <input type="hidden" id="job_type" name="job_type" required>
            </div>
            
            <div class="form-row">
                <label for="job_date">Job Date *</label>
                <input type="date" id="job_date" name="job_date" required>
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
        // Handle button selections
        document.querySelectorAll('.skip-option').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.skip-option').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                document.getElementById('skip_size').value = this.dataset.value;
            });
        });
        
        document.querySelectorAll('.job-option').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.job-option').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                document.getElementById('job_type').value = this.dataset.value;
            });
        });
        
        // Set default date to tomorrow
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        document.getElementById('job_date').value = tomorrow.toISOString().split('T')[0];
    </script>
</body>
</html>
'''

# Inventory Management Template
INVENTORY_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Inventory Management - Tommy's Skips</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: Arial, sans-serif; 
            background: #1a1a1a; 
            color: white; 
            padding: 1rem;
        }
        .header { 
            background: #2c5aa0; 
            padding: 1rem; 
            text-align: center; 
            margin-bottom: 1rem; 
            border-radius: 8px;
        }
        .container { 
            max-width: 1000px; 
            margin: 0 auto;
        }
        .back-btn { 
            background: #666; 
            color: white; 
            padding: 0.5rem 1rem; 
            text-decoration: none; 
            border-radius: 5px; 
            display: inline-block; 
            margin-bottom: 1rem;
        }
        .fleet-panel, .status-panel { 
            background: #2a2a2a; 
            padding: 1.5rem; 
            border-radius: 8px; 
            margin: 1rem 0;
        }
        .fleet-panel h2, .status-panel h2 { 
            color: #ff6b35; 
            margin-bottom: 1rem;
        }
        .fleet-form { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 1rem; 
            margin-bottom: 1rem;
        }
        .fleet-item { 
            background: #333; 
            padding: 1rem; 
            border-radius: 8px;
        }
        .fleet-item label { 
            display: block; 
            color: #ff6b35; 
            margin-bottom: 0.5rem; 
            font-weight: bold;
        }
        .fleet-item input { 
            width: 100%; 
            padding: 0.5rem; 
            background: #444; 
            border: 1px solid #555; 
            border-radius: 5px; 
            color: white; 
            font-size: 1.2rem; 
            text-align: center;
        }
        .current-status { 
            font-size: 0.9rem; 
            color: #ccc; 
            margin-top: 0.5rem;
        }
        .update-btn { 
            background: #ff6b35; 
            color: white; 
            padding: 1rem 2rem; 
            border: none; 
            border-radius: 5px; 
            font-size: 1.1rem; 
            cursor: pointer;
        }
        .update-btn:hover { background: #e55a2b; }
        .overview-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 1rem;
        }
        .overview-item { 
            background: #333; 
            padding: 1rem; 
            border-radius: 8px; 
            text-align: center;
        }
        .overview-item.low-stock { 
            border-left: 4px solid #ff4444; 
            background: #4a2c2c;
        }
        .overview-number { 
            font-size: 2rem; 
            font-weight: bold; 
            color: #ff6b35;
        }
        .overview-label { 
            color: #ccc; 
            margin-top: 0.5rem;
        }
        .breakdown { 
            font-size: 0.9rem; 
            color: #aaa; 
            margin-top: 0.5rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📦 Skip Inventory Management</h1>
    </div>
    
    <div class="container">
        <a href="/" class="back-btn">← Back to Dashboard</a>
        
        <!-- Fleet Size Management -->
        <div class="fleet-panel">
            <h2>🚛 Fleet Size Management</h2>
            <p>Set the total number of skips you own for each size:</p>
            
            <form method="POST" action="/update-fleet">
                <div class="fleet-form">
                    <div class="fleet-item">
                        <label for="mini_total">Mini 4yd Skips</label>
                        <input type="number" id="mini_total" name="mini_total" 
                               value="{{ status.inventory.by_size['Mini 4yd'].total_owned }}" min="0">
                        <div class="current-status">
                            Currently: {{ status.inventory.by_size['Mini 4yd'].out_with_customers }} out, 
                            {{ status.inventory.by_size['Mini 4yd'].available_in_depot }} available
                        </div>
                    </div>
                    
                    <div class="fleet-item">
                        <label for="midi_total">Midi 6yd Skips</label>
                        <input type="number" id="midi_total" name="midi_total" 
                               value="{{ status.inventory.by_size['Midi 6yd'].total_owned }}" min="0">
                        <div class="current-status">
                            Currently: {{ status.inventory.by_size['Midi 6yd'].out_with_customers }} out, 
                            {{ status.inventory.by_size['Midi 6yd'].available_in_depot }} available
                        </div>
                    </div>
                    
                    <div class="fleet-item">
                        <label for="maxi_total">Maxi 8yd Skips</label>
                        <input type="number" id="maxi_total" name="maxi_total" 
                               value="{{ status.inventory.by_size['Maxi 8yd'].total_owned }}" min="0">
                        <div class="current-status">
                            Currently: {{ status.inventory.by_size['Maxi 8yd'].out_with_customers }} out, 
                            {{ status.inventory.by_size['Maxi 8yd'].available_in_depot }} available
                        </div>
                    </div>
                </div>
                
                <button type="submit" class="update-btn">💾 Update Fleet Sizes</button>
            </form>
        </div>
        
        <!-- Current Status Overview -->
        <div class="status-panel">
            <h2>📊 Current Status Overview</h2>
            
            <div class="overview-grid">
                {% for size, data in status.inventory.by_size.items() %}
                <div class="overview-item {{ 'low-stock' if data.utilization_percent >= 80 else '' }}">
                    <div class="overview-number">{{ data.available_in_depot }}</div>
                    <div class="overview-label">{{ size }} Available</div>
                    <div class="breakdown">
                        {{ data.out_with_customers }} out of {{ data.total_owned }} total
                        ({{ data.utilization_percent }}% utilization)
                    </div>
                </div>
                {% endfor %}
                
                <div class="overview-item">
                    <div class="overview-number">{{ status.inventory.totals.total_available }}</div>
                    <div class="overview-label">Total Available</div>
                    <div class="breakdown">
                        {{ status.inventory.totals.total_out }} out of {{ status.inventory.totals.total_owned }} total
                    </div>
                </div>
            </div>
            
            {% if status.alerts %}
            <div style="margin-top: 1.5rem; padding: 1rem; background: #4a2c2c; border-radius: 8px; border-left: 4px solid #ff4444;">
                <h3 style="color: #ff4444; margin-bottom: 0.5rem;">⚠️ Low Stock Alerts:</h3>
                {% for alert in status.alerts %}
                <div style="background: #333; padding: 0.5rem; margin: 0.5rem 0; border-radius: 5px;">
                    {{ alert.message }}
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div style="margin-top: 1.5rem; padding: 1rem; background: #2c4a2c; border-radius: 8px; border-left: 4px solid #44ff44;">
                <h3 style="color: #44ff44;">✅ All skip sizes have good availability</h3>
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
'''

if __name__ == '__main__':
    print("Starting Tommy's Skips - FIXED VERSION")
    init_db()
    print("Access the app at: http://localhost:8082")
    app.run(host='0.0.0.0', port=8082, debug=True)