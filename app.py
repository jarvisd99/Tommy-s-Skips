#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, render_template_string, redirect, url_for, jsonify, flash
import sqlite3
import datetime
import json
import os
from pathlib import Path
from route_optimizer import TommysRouteOptimizer

app = Flask(__name__)
app.secret_key = 'tommys_skips_2026'

# Database initialization
def init_db():
    """Initialize the SQLite database with all required tables"""
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
            customer_type TEXT DEFAULT 'Household',
            company_name TEXT,
            repeat_customer TEXT DEFAULT 'No',
            skip_size TEXT NOT NULL,
            waste_type TEXT DEFAULT 'General',
            permit_needed TEXT DEFAULT 'No',
            job_type TEXT NOT NULL,
            job_date TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            return_date TEXT,
            assigned_truck TEXT DEFAULT 'Iveco',
            assigned_to TEXT NOT NULL,
            placement_instructions TEXT,
            access_issues TEXT,
            notes TEXT,
            payment_method TEXT DEFAULT 'Unpaid',
            price_ex_vat REAL NOT NULL,
            price_inc_vat REAL NOT NULL,
            deposit_amount REAL DEFAULT 0,
            status TEXT DEFAULT 'Booked',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_sync_sheets TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Skip pricing (ex VAT)
SKIP_PRICES = {
    'Mini 4yd': 100.00,
    'Midi 6yd': 141.67,
    'Maxi 8yd': 183.33
}

VAT_RATE = 0.20

def get_price_inc_vat(price_ex_vat):
    """Calculate price including VAT"""
    return price_ex_vat * (1 + VAT_RATE)

def get_vat_amount(price_ex_vat):
    """Calculate VAT amount"""
    return price_ex_vat * VAT_RATE

# Database helper functions
def get_db_connection():
    conn = sqlite3.connect('tommys_skips.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_order_by_id(order_id):
    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    conn.close()
    return order

def get_orders_for_date(date_str):
    conn = get_db_connection()
    orders = conn.execute('SELECT * FROM orders WHERE job_date = ? ORDER BY time_slot', (date_str,)).fetchall()
    conn.close()
    return orders

def get_all_orders():
    conn = get_db_connection()
    orders = conn.execute('SELECT * FROM orders ORDER BY created_at DESC').fetchall()
    conn.close()
    return orders

# Google Sheets sync (placeholder)
def sync_to_google_sheets():
    """Placeholder for Google Sheets synchronization"""
    # This would connect to Google Sheets API and sync all orders
    # For now, just update the last_sync timestamp
    conn = get_db_connection()
    conn.execute('UPDATE orders SET last_sync_sheets = ? WHERE last_sync_sheets IS NULL', 
                (datetime.datetime.now().isoformat(),))
    conn.commit()
    conn.close()
    return True

# Routes
@app.route('/')
def dashboard():
    """Main dashboard showing today's jobs and summary"""
    today = datetime.date.today().isoformat()
    todays_orders = get_orders_for_date(today)
    
    # Calculate today's stats
    total_jobs = len(todays_orders)
    total_revenue_inc_vat = sum(order['price_inc_vat'] for order in todays_orders)
    total_revenue_ex_vat = sum(order['price_ex_vat'] for order in todays_orders)
    
    # Jobs by status
    status_counts = {}
    for order in todays_orders:
        status = order['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Jobs by person
    person_counts = {}
    for order in todays_orders:
        person = order['assigned_to']
        person_counts[person] = person_counts.get(person, 0) + 1
    
    return render_template_string(DASHBOARD_TEMPLATE, 
                                today=today,
                                today_formatted=datetime.date.today().strftime('%A, %d %B %Y'),
                                todays_orders=todays_orders,
                                total_jobs=total_jobs,
                                total_revenue_inc_vat=total_revenue_inc_vat,
                                total_revenue_ex_vat=total_revenue_ex_vat,
                                status_counts=status_counts,
                                person_counts=person_counts)

@app.route('/new', methods=['GET', 'POST'])
def new_order():
    """Create a new order"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        # Get form data
        customer_name = data.get('customer_name', '').strip()
        customer_phone = data.get('customer_phone', '').strip()
        address = data.get('address', '').strip()
        postcode = data.get('postcode', '').strip()
        skip_size = data.get('skip_size', '')
        job_type = data.get('job_type', '')
        job_date = data.get('job_date', datetime.date.today().isoformat())
        time_slot = data.get('time_slot', '')
        assigned_to = data.get('assigned_to', '')
        payment_method = data.get('payment_method', 'Unpaid')
        
        # More details (optional)
        customer_type = data.get('customer_type', 'Household')
        company_name = data.get('company_name', '')
        customer_email = data.get('customer_email', '')
        waste_type = data.get('waste_type', 'General')
        permit_needed = data.get('permit_needed', 'No')
        placement_instructions = data.get('placement_instructions', '')
        access_issues = data.get('access_issues', '')
        return_date = data.get('return_date', '')
        deposit_amount = float(data.get('deposit_amount', 0) or 0)
        notes = data.get('notes', '')
        
        # Validation
        if not all([customer_name, customer_phone, address, postcode, skip_size, job_type, time_slot, assigned_to]):
            if request.is_json:
                return jsonify({'error': 'Please fill in all required fields'}), 400
            flash('Please fill in all required fields')
            return redirect(url_for('new_order'))
        
        # Calculate pricing
        price_ex_vat = SKIP_PRICES.get(skip_size, 100.00)
        price_inc_vat = get_price_inc_vat(price_ex_vat)
        
        # Insert into database
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO orders (
                customer_name, customer_phone, customer_email, address, postcode,
                customer_type, company_name, repeat_customer, skip_size, waste_type,
                permit_needed, job_type, job_date, time_slot, return_date,
                assigned_truck, assigned_to, placement_instructions, access_issues,
                notes, payment_method, price_ex_vat, price_inc_vat, deposit_amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            customer_name, customer_phone, customer_email, address, postcode,
            customer_type, company_name, 'No', skip_size, waste_type,
            permit_needed, job_type, job_date, time_slot, return_date,
            'Iveco', assigned_to, placement_instructions, access_issues,
            notes, payment_method, price_ex_vat, price_inc_vat, deposit_amount
        ))
        conn.commit()
        conn.close()
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Order created successfully'})
        flash('Order created successfully!')
        return redirect(url_for('dashboard'))
    
    # GET request - show form
    today = datetime.date.today().isoformat()
    return render_template_string(NEW_ORDER_TEMPLATE, today=today, skip_prices=SKIP_PRICES)

@app.route('/orders')
def order_list():
    """List all orders with filters"""
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')
    person_filter = request.args.get('assigned_to', '')
    
    conn = get_db_connection()
    
    query = 'SELECT * FROM orders WHERE 1=1'
    params = []
    
    if search:
        query += ' AND (customer_name LIKE ? OR address LIKE ? OR postcode LIKE ?)'
        search_param = f'%{search}%'
        params.extend([search_param, search_param, search_param])
    
    if status_filter:
        query += ' AND status = ?'
        params.append(status_filter)
    
    if person_filter:
        query += ' AND assigned_to = ?'
        params.append(person_filter)
    
    query += ' ORDER BY created_at DESC'
    
    orders = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template_string(ORDER_LIST_TEMPLATE, 
                                orders=orders, 
                                search=search, 
                                status_filter=status_filter,
                                person_filter=person_filter)

@app.route('/order/<int:order_id>')
def order_detail(order_id):
    """View and edit order details"""
    order = get_order_by_id(order_id)
    if not order:
        flash('Order not found')
        return redirect(url_for('order_list'))
    
    return render_template_string(ORDER_DETAIL_TEMPLATE, order=order)

@app.route('/order/<int:order_id>/status', methods=['POST'])
def update_order_status(order_id):
    """Update order status"""
    new_status = request.json.get('status') if request.is_json else request.form.get('status')
    
    if new_status not in ['Booked', 'Delivered', 'Collected', 'Complete']:
        return jsonify({'error': 'Invalid status'}), 400
    
    conn = get_db_connection()
    conn.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, order_id))
    conn.commit()
    conn.close()
    
    if request.is_json:
        return jsonify({'success': True})
    
    flash(f'Order status updated to {new_status}')
    return redirect(url_for('order_detail', order_id=order_id))

@app.route('/sync-sheets', methods=['POST'])
def sync_sheets():
    """Manually sync to Google Sheets"""
    try:
        sync_to_google_sheets()
        if request.is_json:
            return jsonify({'success': True, 'message': 'Synced to Google Sheets'})
        flash('Successfully synced to Google Sheets')
    except Exception as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash(f'Sync failed: {str(e)}')
    
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/routes')
def route_optimizer_page():
    """Daily route optimization page"""
    try:
        optimizer = TommysRouteOptimizer(api_key=os.getenv('GOOGLE_MAPS_API_KEY'))
        
        # Get date from request or use today
        selected_date = request.args.get('date', datetime.datetime.now().strftime('%Y-%m-%d'))
        
        # Optimize route for selected date
        route_result = optimizer.optimize_daily_route(selected_date)
        
        return render_template_string(ROUTE_TEMPLATE, 
                                    route_data=route_result,
                                    selected_date=selected_date)
    except Exception as e:
        flash(f'Route optimization error: {str(e)}')
        return redirect(url_for('dashboard'))

@app.route('/routes/update-pickup/<int:order_id>', methods=['POST'])
def update_pickup_status(order_id):
    """Update pickup status for completed pickups"""
    try:
        optimizer = TommysRouteOptimizer()
        optimizer.update_pickup_status(order_id, 'Completed')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stats')
def stats_page():
    """Business statistics and insights"""
    conn = sqlite3.connect('tommys_skips.db')
    cursor = conn.cursor()
    
    # All orders
    cursor.execute('SELECT * FROM orders ORDER BY job_date DESC')
    columns = [desc[0] for desc in cursor.description]
    all_orders = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # Revenue by day
    cursor.execute('''
        SELECT job_date, COUNT(*) as jobs, SUM(price_inc_vat) as revenue_inc, SUM(price_ex_vat) as revenue_ex
        FROM orders GROUP BY job_date ORDER BY job_date DESC LIMIT 30
    ''')
    daily_stats = cursor.fetchall()
    
    # Revenue by day of week
    cursor.execute('''
        SELECT 
            CASE CAST(strftime('%w', job_date) AS INTEGER)
                WHEN 0 THEN 'Sunday' WHEN 1 THEN 'Monday' WHEN 2 THEN 'Tuesday'
                WHEN 3 THEN 'Wednesday' WHEN 4 THEN 'Thursday' WHEN 5 THEN 'Friday'
                WHEN 6 THEN 'Saturday' END as day_name,
            CAST(strftime('%w', job_date) AS INTEGER) as day_num,
            COUNT(*) as jobs, SUM(price_inc_vat) as revenue
        FROM orders GROUP BY day_num ORDER BY day_num
    ''')
    weekday_stats = cursor.fetchall()
    
    # By person
    cursor.execute('''
        SELECT assigned_to, COUNT(*) as jobs, SUM(price_inc_vat) as revenue
        FROM orders GROUP BY assigned_to ORDER BY revenue DESC
    ''')
    person_stats = cursor.fetchall()
    
    # By skip size
    cursor.execute('''
        SELECT skip_size, COUNT(*) as jobs, SUM(price_inc_vat) as revenue
        FROM orders GROUP BY skip_size ORDER BY jobs DESC
    ''')
    skip_stats = cursor.fetchall()
    
    # By time slot
    cursor.execute('''
        SELECT time_slot, COUNT(*) as jobs, SUM(price_inc_vat) as revenue
        FROM orders GROUP BY time_slot ORDER BY jobs DESC
    ''')
    slot_stats = cursor.fetchall()
    
    # By payment method
    cursor.execute('''
        SELECT payment_method, COUNT(*) as jobs, SUM(price_inc_vat) as revenue
        FROM orders GROUP BY payment_method ORDER BY jobs DESC
    ''')
    payment_stats = cursor.fetchall()
    
    # Totals
    cursor.execute('SELECT COUNT(*) as total, SUM(price_inc_vat) as rev_inc, SUM(price_ex_vat) as rev_ex FROM orders')
    totals = cursor.fetchone()
    
    # This week
    cursor.execute('''
        SELECT COUNT(*) as total, COALESCE(SUM(price_inc_vat),0) as rev
        FROM orders WHERE job_date >= date('now', '-7 days')
    ''')
    week_stats = cursor.fetchone()
    
    # This month
    cursor.execute('''
        SELECT COUNT(*) as total, COALESCE(SUM(price_inc_vat),0) as rev
        FROM orders WHERE job_date >= date('now', 'start of month')
    ''')
    month_stats = cursor.fetchone()
    
    # Busiest day ever
    cursor.execute('''
        SELECT job_date, COUNT(*) as jobs, SUM(price_inc_vat) as revenue
        FROM orders GROUP BY job_date ORDER BY jobs DESC LIMIT 1
    ''')
    busiest_day = cursor.fetchone()
    
    # Highest revenue day
    cursor.execute('''
        SELECT job_date, COUNT(*) as jobs, SUM(price_inc_vat) as revenue
        FROM orders GROUP BY job_date ORDER BY revenue DESC LIMIT 1
    ''')
    highest_rev_day = cursor.fetchone()
    
    conn.close()
    
    return render_template_string(STATS_TEMPLATE,
        daily_stats=daily_stats,
        weekday_stats=weekday_stats,
        person_stats=person_stats,
        skip_stats=skip_stats,
        slot_stats=slot_stats,
        payment_stats=payment_stats,
        totals=totals,
        week_stats=week_stats,
        month_stats=month_stats,
        busiest_day=busiest_day,
        highest_rev_day=highest_rev_day)

STATS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="30">
    <title>Stats - Tommy's Skips</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f1923;
            --card: #1a2836;
            --card-dark: #152230;
            --orange: #ff8c00;
            --yellow: #ffb347;
            --green: #00c853;
            --red: #ff4444;
            --white: #ffffff;
            --subtle: #8899aa;
            --border: #2a3a4a;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg);
            color: var(--white);
            min-height: 100vh;
            padding-bottom: 120px;
        }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        h1 { font-family: 'Poppins', sans-serif; font-size: 1.5rem; margin-bottom: 20px; color: var(--orange); }
        h2 { font-family: 'Poppins', sans-serif; font-size: 1.1rem; margin: 20px 0 10px; color: var(--yellow); }
        
        .stat-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: var(--card);
            border-radius: 12px;
            padding: 16px;
            border: 1px solid var(--border);
            text-align: center;
        }
        
        .stat-card.wide { grid-column: 1 / -1; }
        
        .stat-value {
            font-family: 'Poppins', sans-serif;
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--orange);
        }
        
        .stat-label {
            font-size: 0.8rem;
            color: var(--subtle);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 4px;
        }
        
        .stat-table {
            width: 100%;
            background: var(--card);
            border-radius: 12px;
            border: 1px solid var(--border);
            overflow: hidden;
            margin-bottom: 15px;
        }
        
        .stat-table th {
            background: var(--card-dark);
            padding: 12px 15px;
            text-align: left;
            font-size: 0.8rem;
            color: var(--subtle);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid var(--border);
        }
        
        .stat-table td {
            padding: 12px 15px;
            border-bottom: 1px solid var(--border);
            font-family: 'Inter', sans-serif;
            font-size: 0.95rem;
        }
        
        .stat-table tr:last-child td { border-bottom: none; }
        
        .stat-table .revenue { color: var(--green); font-weight: 600; }
        .stat-table .jobs { color: var(--orange); font-weight: 600; }
        
        .bar-container {
            background: var(--card-dark);
            border-radius: 6px;
            height: 24px;
            overflow: hidden;
            margin-top: 4px;
        }
        
        .bar-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--orange), var(--yellow));
            border-radius: 6px;
            transition: width 0.5s;
            display: flex;
            align-items: center;
            padding-left: 8px;
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--bg);
        }
        
        .record-card {
            background: var(--card);
            border-radius: 12px;
            padding: 16px;
            border: 1px solid var(--border);
            border-left: 4px solid var(--green);
            margin-bottom: 10px;
        }
        
        .record-label { font-size: 0.8rem; color: var(--subtle); text-transform: uppercase; }
        .record-value { font-size: 1.2rem; font-weight: 700; color: var(--white); margin-top: 4px; }
        .record-detail { font-size: 0.85rem; color: var(--subtle); margin-top: 2px; }
        
        .bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: var(--card-dark);
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: space-around;
            padding: 8px 0 12px;
            z-index: 1000;
        }
        .nav-item {
            text-align: center;
            text-decoration: none;
            color: var(--subtle);
            font-size: 0.7rem;
            font-weight: 500;
            padding: 4px 12px;
            transition: color 0.2s;
        }
        .nav-item.active { color: var(--orange); }
        .nav-icon { font-size: 0.75rem; font-weight: 700; color: var(--orange); letter-spacing: 1px; margin-bottom: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>&#128202; Business Stats</h1>
        
        <!-- Overview Cards -->
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-value">{{ totals[0] or 0 }}</div>
                <div class="stat-label">Total Jobs</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">&pound;{{ "%.0f"|format(totals[1] or 0) }}</div>
                <div class="stat-label">Total Revenue</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ week_stats[0] or 0 }}</div>
                <div class="stat-label">This Week</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">&pound;{{ "%.0f"|format(week_stats[1] or 0) }}</div>
                <div class="stat-label">Week Revenue</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ month_stats[0] or 0 }}</div>
                <div class="stat-label">This Month</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">&pound;{{ "%.0f"|format(month_stats[1] or 0) }}</div>
                <div class="stat-label">Month Revenue</div>
            </div>
            <div class="stat-card wide">
                <div class="stat-value">&pound;{{ "%.0f"|format(totals[2] or 0) }}</div>
                <div class="stat-label">Total Revenue (ex VAT)</div>
            </div>
        </div>
        
        <!-- Records -->
        <h2>&#127942; Records</h2>
        {% if busiest_day %}
        <div class="record-card">
            <div class="record-label">Busiest Day</div>
            <div class="record-value">{{ busiest_day[1] }} jobs</div>
            <div class="record-detail">{{ busiest_day[0] }} - &pound;{{ "%.0f"|format(busiest_day[2] or 0) }} revenue</div>
        </div>
        {% endif %}
        {% if highest_rev_day %}
        <div class="record-card" style="border-left-color: var(--orange);">
            <div class="record-label">Highest Revenue Day</div>
            <div class="record-value">&pound;{{ "%.0f"|format(highest_rev_day[2] or 0) }}</div>
            <div class="record-detail">{{ highest_rev_day[0] }} - {{ highest_rev_day[1] }} jobs</div>
        </div>
        {% endif %}
        
        <!-- Busiest Days of Week -->
        <h2>&#128197; Busiest Days of Week</h2>
        {% if weekday_stats %}
        {% set max_jobs = weekday_stats|map(attribute=2)|max if weekday_stats else 1 %}
        {% for day in weekday_stats %}
        <div style="margin-bottom: 8px;">
            <div style="display:flex;justify-content:space-between;font-size:0.9rem;margin-bottom:2px">
                <span>{{ day[0] }}</span>
                <span><span class="jobs">{{ day[2] }} jobs</span> &middot; <span class="revenue">&pound;{{ "%.0f"|format(day[3] or 0) }}</span></span>
            </div>
            <div class="bar-container">
                <div class="bar-fill" style="width: {{ (day[2] / max_jobs * 100)|int }}%">{{ day[2] }}</div>
            </div>
        </div>
        {% endfor %}
        {% else %}
        <p style="color:var(--subtle)">No data yet</p>
        {% endif %}
        
        <!-- Revenue by Person -->
        <h2>&#128104;&#8205;&#128736; Jobs by Person</h2>
        <table class="stat-table">
            <thead><tr><th>Person</th><th>Jobs</th><th>Revenue</th></tr></thead>
            <tbody>
            {% for person in person_stats %}
            <tr>
                <td>{{ person[0] }}</td>
                <td class="jobs">{{ person[1] }}</td>
                <td class="revenue">&pound;{{ "%.2f"|format(person[2] or 0) }}</td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
        
        <!-- Skip Size Breakdown -->
        <h2>&#128230; Skip Sizes</h2>
        <table class="stat-table">
            <thead><tr><th>Size</th><th>Jobs</th><th>Revenue</th></tr></thead>
            <tbody>
            {% for skip in skip_stats %}
            <tr>
                <td>{{ skip[0] }}</td>
                <td class="jobs">{{ skip[1] }}</td>
                <td class="revenue">&pound;{{ "%.2f"|format(skip[2] or 0) }}</td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
        
        <!-- Time Slot Breakdown -->
        <h2>&#9200; Time Slots</h2>
        <table class="stat-table">
            <thead><tr><th>Slot</th><th>Jobs</th><th>Revenue</th></tr></thead>
            <tbody>
            {% for slot in slot_stats %}
            <tr>
                <td>{{ slot[0] }}</td>
                <td class="jobs">{{ slot[1] }}</td>
                <td class="revenue">&pound;{{ "%.2f"|format(slot[2] or 0) }}</td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
        
        <!-- Payment Methods -->
        <h2>&#128179; Payment Methods</h2>
        <table class="stat-table">
            <thead><tr><th>Method</th><th>Jobs</th><th>Revenue</th></tr></thead>
            <tbody>
            {% for pay in payment_stats %}
            <tr>
                <td>{{ pay[0] }}</td>
                <td class="jobs">{{ pay[1] }}</td>
                <td class="revenue">&pound;{{ "%.2f"|format(pay[2] or 0) }}</td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
        
        <!-- Recent Daily Revenue -->
        <h2>&#128200; Daily Revenue (Last 30 Days)</h2>
        <table class="stat-table">
            <thead><tr><th>Date</th><th>Jobs</th><th>Revenue</th></tr></thead>
            <tbody>
            {% for day in daily_stats %}
            <tr>
                <td>{{ day[0] }}</td>
                <td class="jobs">{{ day[1] }}</td>
                <td class="revenue">&pound;{{ "%.2f"|format(day[2] or 0) }}</td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
    
    <nav class="bottom-nav">
        <a href="/" class="nav-item">
            <div class="nav-icon">HOME</div>
            Dashboard
        </a>
        <a href="/new" class="nav-item">
            <div class="nav-icon">+ NEW</div>
            New Order
        </a>
        <a href="/orders" class="nav-item">
            <div class="nav-icon">LIST</div>
            All Orders
        </a>
        <a href="/stats" class="nav-item active">
            <div class="nav-icon">STATS</div>
            Stats
        </a>
    </nav>
</body>
</html>
'''

# Templates
DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="30">
    <title>Dashboard - Tommy's Skips</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #0f1923;
            --card-dark: #1a2836;
            --orange: #ff8c00;
            --yellow: #ffb347;
            --green: #00c853;
            --white: #ffffff;
            --subtle: #8899aa;
            --border: #2a3a4a;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg-dark);
            color: var(--white);
            min-height: 100vh;
            padding-bottom: 120px;
        }
        
        .header {
            background: var(--card-dark);
            padding: 1rem;
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header h1 {
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            color: var(--orange);
            font-size: 1.5rem;
        }
        
        .header .subtitle {
            color: var(--subtle);
            font-size: 0.9rem;
            margin-top: 0.25rem;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 1rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: var(--card-dark);
            border-radius: 12px;
            padding: 1rem;
            border: 1px solid var(--border);
            text-align: center;
        }
        
        .stat-value {
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            font-size: 1.5rem;
            color: var(--orange);
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            font-size: 0.8rem;
            color: var(--subtle);
        }
        
        .quick-add-btn {
            background: linear-gradient(135deg, var(--orange), var(--yellow));
            color: var(--white);
            border: none;
            border-radius: 16px;
            padding: 1rem 2rem;
            font-size: 1.1rem;
            font-weight: 600;
            margin: 1rem 0 2rem;
            width: 100%;
            min-height: 60px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }
        
        .quick-add-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(255, 140, 0, 0.3);
        }
        
        .orders-section h2 {
            font-family: 'Poppins', sans-serif;
            color: var(--white);
            margin-bottom: 1rem;
            font-size: 1.3rem;
        }
        
        .order-card {
            background: var(--card-dark);
            border-radius: 12px;
            padding: 1rem 1rem 0.75rem;
            border: 1px solid var(--border);
            margin-bottom: 1rem;
            border-left: 4px solid var(--orange);
            display: block;
            overflow: visible;
        }
        
        .order-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        .customer-name {
            font-weight: 600;
            font-size: 1.05rem;
            color: var(--white);
        }
        
        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .status-booked { background: #1565c0; color: white; }
        .status-delivered { background: var(--yellow); color: #333; }
        .status-collected { background: var(--orange); color: white; }
        .status-complete { background: var(--green); color: white; }
        
        .order-details {
            color: var(--subtle);
            font-size: 0.9rem;
            line-height: 1.5;
            margin-bottom: 0.5rem;
        }
        
        .order-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 0.5rem;
            border-top: 1px solid var(--border);
        }
        
        .order-meta span {
            font-size: 0.9rem;
            color: var(--subtle);
        }
        
        .price {
            color: var(--orange);
            font-weight: 700;
            font-size: 1.1rem;
        }
        
        .bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: var(--card-dark);
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: space-around;
            padding: 0.75rem 0;
        }
        
        .nav-item {
            text-decoration: none;
            color: var(--subtle);
            text-align: center;
            font-size: 0.75rem;
            padding: 0.5rem;
            flex: 1;
        }
        
        .nav-item.active {
            color: var(--orange);
        }
        
        .nav-item:hover {
            color: var(--white);
        }
        
        .nav-icon { font-size: 0.75rem; font-weight: 700; color: var(--orange); letter-spacing: 1px; margin-bottom: 4px; }
        
        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Tommy's Skips</h1>
        <div class="subtitle">{{ today_formatted }}</div>
    </div>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{{ total_jobs }}</div>
                <div class="stat-label">Jobs Today</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">&pound;{{ "%.2f"|format(total_revenue_inc_vat) }}</div>
                <div class="stat-label">Revenue (Inc VAT)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ person_counts.get('Rob', 0) }}</div>
                <div class="stat-label">Rob's Jobs</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ person_counts.get('Tommy', 0) }}</div>
                <div class="stat-label">Tommy's Jobs</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ person_counts.get('John', 0) }}</div>
                <div class="stat-label">John's Jobs</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ status_counts.get('Complete', 0) }}</div>
                <div class="stat-label">Complete</div>
            </div>
        </div>
        
        <a href="{{ url_for('new_order') }}" class="quick-add-btn">+ Add New Order
        </a>
        
        <a href="{{ url_for('route_optimizer_page') }}" class="quick-add-btn" style="background: linear-gradient(135deg, #2c5aa0, #4285F4); margin-top: 0.5rem;">🗺️ Daily Routes
        </a>
        
        <div class="orders-section">
            <h2>Today's Orders</h2>
            
            {% if todays_orders %}
                {% for order in todays_orders %}
                <a href="{{ url_for('order_detail', order_id=order.id) }}" class="order-card" style="text-decoration: none; color: inherit;">
                    <div class="order-header">
                        <div class="customer-name">{{ order.customer_name }}</div>
                        <div class="status-badge status-{{ order.status.lower() }}">{{ order.status }}</div>
                    </div>
                    <div class="order-details">
                        {{ order.skip_size }}  |  {{ order.job_type }}  |  {{ order.time_slot }}<br>
                        {{ order.address }}, {{ order.postcode }}
                    </div>
                    <div class="order-meta">
                        <span>{{ order.assigned_to }}</span>
                        <span class="price">&pound;{{ "%.2f"|format(order.price_inc_vat) }}</span>
                    </div>
                </a>
                {% endfor %}
            {% else %}
                <div class="order-card">
                    <div style="text-align: center; color: var(--subtle);">
                        No orders scheduled for today
                    </div>
                </div>
            {% endif %}
        </div>
    </div>
    
    <nav class="bottom-nav">
        <a href="{{ url_for('dashboard') }}" class="nav-item active">
            <div class="nav-icon">HOME</div>
            Dashboard
        </a>
        <a href="{{ url_for('new_order') }}" class="nav-item">
            <div class="nav-icon">+ NEW</div>
            New Order
        </a>
        <a href="{{ url_for('order_list') }}" class="nav-item">
            <div class="nav-icon">LIST</div>
            All Orders
        </a>
        <a href="/stats" class="nav-item"><div class="nav-icon">STATS</div>
            Stats</a>
    </nav>
    
    <script>
        function syncSheets(event) {
            event.preventDefault();
            if (confirm('Sync all orders to Google Sheets?')) {
                fetch('/sync-sheets', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Successfully synced to Google Sheets');
                        } else {
                            alert('Sync failed: ' + data.error);
                        }
                    })
                    .catch(err => alert('Sync failed: ' + err.message));
            }
            return false;
        }
    </script>
</body>
</html>
'''

NEW_ORDER_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="30">
    <title>New Order - Tommy's Skips</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #0f1923;
            --card-dark: #1a2836;
            --orange: #ff8c00;
            --yellow: #ffb347;
            --green: #00c853;
            --white: #ffffff;
            --subtle: #8899aa;
            --border: #2a3a4a;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg-dark);
            color: var(--white);
            min-height: 100vh;
            padding-bottom: 120px;
        }
        
        .header {
            background: var(--card-dark);
            padding: 1rem;
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header h1 {
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            color: var(--orange);
            font-size: 1.5rem;
        }
        
        .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 1rem;
        }
        
        .form-section {
            background: var(--card-dark);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid var(--border);
            margin-bottom: 1rem;
        }
        
        .section-title {
            font-family: 'Poppins', sans-serif;
            font-weight: 600;
            color: var(--orange);
            margin-bottom: 1rem;
            font-size: 1.1rem;
        }
        
        .form-row {
            margin-bottom: 1rem;
        }
        
        .form-row.half {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }
        
        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: var(--white);
        }
        
        input[type="text"], input[type="tel"], input[type="email"], input[type="date"], textarea {
            width: 100%;
            padding: 1rem;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--bg-dark);
            color: var(--white);
            font-size: 1rem;
            min-height: 48px;
        }
        
        input[type="text"]:focus, input[type="tel"]:focus, input[type="email"]:focus, input[type="date"]:focus, textarea:focus {
            outline: none;
            border-color: var(--orange);
        }
        
        textarea {
            resize: vertical;
            min-height: 80px;
        }
        
        .button-group {
            display: grid;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }
        
        .button-group.three {
            grid-template-columns: repeat(3, 1fr);
        }
        
        .button-group.four {
            grid-template-columns: repeat(2, 1fr);
            grid-template-rows: repeat(2, 1fr);
        }
        
        .button-group.two {
            grid-template-columns: repeat(2, 1fr);
        }
        
        .btn {
            padding: 1rem;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--bg-dark);
            color: var(--white);
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            min-height: 56px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
        }
        
        .btn:hover {
            border-color: var(--orange);
        }
        
        .btn.active {
            background: var(--orange);
            border-color: var(--orange);
            color: var(--white);
        }
        
        .btn.skip-size {
            flex-direction: column;
            padding: 0.75rem 0.5rem;
        }
        
        .skip-size .size {
            font-weight: 700;
            font-size: 1rem;
        }
        
        .skip-size .price {
            font-size: 0.8rem;
            color: var(--green);
            margin-top: 0.25rem;
        }
        
        .submit-btn {
            background: linear-gradient(135deg, var(--orange), var(--yellow));
            color: var(--white);
            border: none;
            border-radius: 16px;
            padding: 1.25rem 2rem;
            font-size: 1.2rem;
            font-weight: 600;
            width: 100%;
            min-height: 64px;
            cursor: pointer;
            margin-top: 1rem;
        }
        
        .submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(255, 140, 0, 0.3);
        }
        
        .more-details {
            margin-top: 1rem;
        }
        
        .expand-toggle {
            background: var(--border);
            color: var(--white);
            border: none;
            border-radius: 8px;
            padding: 1rem;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            width: 100%;
            margin-bottom: 1rem;
        }
        
        .expand-toggle:hover {
            background: var(--subtle);
        }
        
        .details-content {
            display: none;
        }
        
        .details-content.expanded {
            display: block;
        }
        
        .bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: var(--card-dark);
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: space-around;
            padding: 0.75rem 0;
        }
        
        .nav-item {
            text-decoration: none;
            color: var(--subtle);
            text-align: center;
            font-size: 0.75rem;
            padding: 0.5rem;
            flex: 1;
        }
        
        .nav-item.active {
            color: var(--orange);
        }
        
        .nav-item:hover {
            color: var(--white);
        }
        
        .nav-icon { font-size: 0.75rem; font-weight: 700; color: var(--orange); letter-spacing: 1px; margin-bottom: 4px; }
        
        @media (max-width: 480px) {
            .button-group.four {
                grid-template-columns: 1fr;
                grid-template-rows: auto;
            }
            
            .form-row.half {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>New Order</h1>
    </div>
    
    <div class="container">
        <form id="orderForm" method="POST">
            <!-- Main Form (Always Visible) -->
            <div class="form-section">
                <div class="section-title">Order Details</div>
                
                <div class="form-row">
                    <label for="customer_name">Customer Name *</label>
                    <input type="text" id="customer_name" name="customer_name" required>
                </div>
                
                <div class="form-row half">
                    <div>
                        <label for="customer_phone">Phone *</label>
                        <input type="tel" id="customer_phone" name="customer_phone" required>
                    </div>
                    <div>
                        <label for="postcode">Postcode *</label>
                        <input type="text" id="postcode" name="postcode" required>
                    </div>
                </div>
                
                <div class="form-row">
                    <label for="address">Address *</label>
                    <input type="text" id="address" name="address" required>
                </div>
                
                <div class="form-row">
                    <label>Skip Size *</label>
                    <div class="button-group three">
                        <button type="button" class="btn btn-option skip-size" data-field="skip_size" data-value="Mini 4yd">
                            <div class="size">Mini 4yd</div>
                            <div class="price">&pound;120</div>
                        </button>
                        <button type="button" class="btn btn-option skip-size" data-field="skip_size" data-value="Midi 6yd">
                            <div class="size">Midi 6yd</div>
                            <div class="price">&pound;170</div>
                        </button>
                        <button type="button" class="btn btn-option skip-size" data-field="skip_size" data-value="Maxi 8yd">
                            <div class="size">Maxi 8yd</div>
                            <div class="price">&pound;220</div>
                        </button>
                    </div>
                    <input type="hidden" id="skip_size" name="skip_size" required>
                </div>
                
                <div class="form-row">
                    <label>Job Type *</label>
                    <div class="button-group three">
                        <button type="button" class="btn btn-option" data-field="job_type" data-value="Deliver">Deliver</button>
                        <button type="button" class="btn btn-option" data-field="job_type" data-value="Collect">Collect</button>
                        <button type="button" class="btn btn-option" data-field="job_type" data-value="Swap">Swap</button>
                    </div>
                    <input type="hidden" id="job_type" name="job_type" required>
                </div>
                
                <div class="form-row half">
                    <div>
                        <label for="job_date">Date *</label>
                        <input type="date" id="job_date" name="job_date" value="{{ today }}" required>
                    </div>
                    <div>
                        <label>Time Slot *</label>
                        <div class="button-group four">
                            <button type="button" class="btn btn-option" data-field="time_slot" data-value="Early Morning (7am-9am)">Early AM</button>
                            <button type="button" class="btn btn-option" data-field="time_slot" data-value="Morning (9am-12pm)">Morning</button>
                            <button type="button" class="btn btn-option" data-field="time_slot" data-value="Afternoon (12pm-3pm)">Afternoon</button>
                            <button type="button" class="btn btn-option" data-field="time_slot" data-value="Late Afternoon (3pm-5pm)">Late PM</button>
                        </div>
                        <input type="hidden" id="time_slot" name="time_slot" required>
                    </div>
                </div>
                
                <div class="form-row">
                    <label>Assigned To *</label>
                    <div class="button-group three">
                        <button type="button" class="btn btn-option" data-field="assigned_to" data-value="Rob">Rob</button>
                        <button type="button" class="btn btn-option" data-field="assigned_to" data-value="Tommy">Tommy</button>
                        <button type="button" class="btn btn-option" data-field="assigned_to" data-value="John">John</button>
                    </div>
                    <input type="hidden" id="assigned_to" name="assigned_to" required>
                </div>
                
                <div class="form-row">
                    <label>Payment *</label>
                    <div class="button-group four">
                        <button type="button" class="btn btn-option" data-field="payment_method" data-value="Cash">Cash</button>
                        <button type="button" class="btn btn-option" data-field="payment_method" data-value="Card">Card</button>
                        <button type="button" class="btn btn-option" data-field="payment_method" data-value="Bank Transfer">Transfer</button>
                        <button type="button" class="btn btn-option" data-field="payment_method" data-value="Unpaid">Unpaid</button>
                    </div>
                    <input type="hidden" id="payment_method" name="payment_method" value="Unpaid">
                </div>
            </div>
            
            <!-- + More Details (Collapsible) -->
            <div class="more-details">
                <button type="button" class="expand-toggle" onclick="toggleDetails()">
                    " + More Details (Optional)
                </button>
                
                <div class="details-content" id="detailsContent">
                    <div class="form-section">
                        <div class="form-row">
                            <label>Customer Type</label>
                            <div class="button-group two">
                                <button type="button" class="btn btn-option active" data-field="customer_type" data-value="Household">Household</button>
                                <button type="button" class="btn btn-option" data-field="customer_type" data-value="Business">Business</button>
                            </div>
                            <input type="hidden" id="customer_type" name="customer_type" value="Household">
                        </div>
                        
                        <div class="form-row" id="company_row" style="display: none;">
                            <label for="company_name">Company Name</label>
                            <input type="text" id="company_name" name="company_name">
                        </div>
                        
                        <div class="form-row">
                            <label for="customer_email">Customer Email</label>
                            <input type="email" id="customer_email" name="customer_email">
                        </div>
                        
                        <div class="form-row">
                            <label>Waste Type</label>
                            <div class="button-group four">
                                <button type="button" class="btn btn-option active" data-field="waste_type" data-value="General">General</button>
                                <button type="button" class="btn btn-option" data-field="waste_type" data-value="Soil">Soil</button>
                                <button type="button" class="btn btn-option" data-field="waste_type" data-value="Rubble">Rubble</button>
                                <button type="button" class="btn btn-option" data-field="waste_type" data-value="Mixed">Mixed</button>
                            </div>
                            <input type="hidden" id="waste_type" name="waste_type" value="General">
                        </div>
                        
                        <div class="form-row">
                            <label>Permit Needed?</label>
                            <div class="button-group two">
                                <button type="button" class="btn btn-option active" data-field="permit_needed" data-value="No">No</button>
                                <button type="button" class="btn btn-option" data-field="permit_needed" data-value="Yes">Yes</button>
                            </div>
                            <input type="hidden" id="permit_needed" name="permit_needed" value="No">
                        </div>
                        
                        <div class="form-row">
                            <label for="placement_instructions">Placement Instructions</label>
                            <input type="text" id="placement_instructions" name="placement_instructions" placeholder="e.g. front driveway, back garden">
                        </div>
                        
                        <div class="form-row">
                            <label for="access_issues">Access Issues</label>
                            <input type="text" id="access_issues" name="access_issues" placeholder="e.g. narrow road, low bridge">
                        </div>
                        
                        <div class="form-row half">
                            <div>
                                <label for="return_date">Return Date</label>
                                <input type="date" id="return_date" name="return_date">
                            </div>
                            <div>
                                <label for="deposit_amount">Deposit Amount (&pound;)</label>
                                <input type="text" id="deposit_amount" name="deposit_amount" placeholder="0.00">
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <label for="notes">Additional Notes</label>
                            <textarea id="notes" name="notes" placeholder="Any additional information"></textarea>
                        </div>
                    </div>
                </div>
            </div>
            
            <button type="submit" class="submit-btn">' SAVE ORDER</button>
        </form>
    </div>
    
    <nav class="bottom-nav">
        <a href="{{ url_for('dashboard') }}" class="nav-item">
            <div class="nav-icon">HOME</div>
            Dashboard
        </a>
        <a href="{{ url_for('new_order') }}" class="nav-item active">
            <div class="nav-icon">+ NEW</div>
            New Order
        </a>
        <a href="{{ url_for('order_list') }}" class="nav-item">
            <div class="nav-icon">LIST</div>
            All Orders
        </a>
        <a href="/stats" class="nav-item"><div class="nav-icon">STATS</div>
            Stats</a>
    </nav>
    
    <script>
        // Button group selection
        document.querySelectorAll('.btn-option').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                
                const field = this.dataset.field;
                const value = this.dataset.value;
                
                // Remove active class from siblings
                this.parentNode.querySelectorAll('.btn-option').forEach(sibling => {
                    sibling.classList.remove('active');
                });
                
                // Add active class to clicked button
                this.classList.add('active');
                
                // Update hidden input
                document.getElementById(field).value = value;
                
                // Show/hide company name field based on customer type
                if (field === 'customer_type') {
                    const companyRow = document.getElementById('company_row');
                    if (value === 'Business') {
                        companyRow.style.display = 'block';
                    } else {
                        companyRow.style.display = 'none';
                        document.getElementById('company_name').value = '';
                    }
                }
            });
        });
        
        // Toggle more details section
        function toggleDetails() {
            const content = document.getElementById('detailsContent');
            const toggle = document.querySelector('.expand-toggle');
            
            if (content.classList.contains('expanded')) {
                content.classList.remove('expanded');
                toggle.textContent = '" + More Details (Optional)';
            } else {
                content.classList.add('expanded');
                toggle.textContent = '" - Hide Details';
            }
        }
        
        // Form submission
        document.getElementById('orderForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Validate required fields
            const required = ['customer_name', 'customer_phone', 'address', 'postcode', 'skip_size', 'job_type', 'time_slot', 'assigned_to'];
            let valid = true;
            
            required.forEach(field => {
                const input = document.getElementById(field);
                if (!input.value.trim()) {
                    valid = false;
                    input.style.borderColor = '#ff4444';
                } else {
                    input.style.borderColor = '';
                }
            });
            
            if (!valid) {
                alert('Please fill in all required fields');
                return;
            }
            
            // Submit form
            const formData = new FormData(this);
            const submitBtn = document.querySelector('.submit-btn');
            submitBtn.textContent = 'Saving...';
            submitBtn.disabled = true;
            
            fetch('/new', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (response.redirected) {
                    window.location.href = response.url;
                } else {
                    return response.json();
                }
            })
            .then(data => {
                if (data && data.error) {
                    alert(data.error);
                } else if (data && data.success) {
                    window.location.href = '/';
                }
            })
            .catch(err => {
                alert('Error saving order: ' + err.message);
            })
            .finally(() => {
                submitBtn.textContent = '' SAVE ORDER';
                submitBtn.disabled = false;
            });
        });
        
        function syncSheets(event) {
            event.preventDefault();
            if (confirm('Sync all orders to Google Sheets?')) {
                fetch('/sync-sheets', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Successfully synced to Google Sheets');
                        } else {
                            alert('Sync failed: ' + data.error);
                        }
                    })
                    .catch(err => alert('Sync failed: ' + err.message));
            }
            return false;
        }
    </script>
</body>
</html>
'''

ORDER_LIST_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="30">
    <title>All Orders - Tommy's Skips</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #0f1923;
            --card-dark: #1a2836;
            --orange: #ff8c00;
            --yellow: #ffb347;
            --green: #00c853;
            --white: #ffffff;
            --subtle: #8899aa;
            --border: #2a3a4a;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg-dark);
            color: var(--white);
            min-height: 100vh;
            padding-bottom: 120px;
        }
        
        .header {
            background: var(--card-dark);
            padding: 1rem;
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header h1 {
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            color: var(--orange);
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }
        
        .filters {
            display: grid;
            grid-template-columns: 1fr auto auto;
            gap: 0.5rem;
            align-items: center;
        }
        
        .search-input {
            padding: 0.75rem;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--bg-dark);
            color: var(--white);
            font-size: 1rem;
        }
        
        .filter-select {
            padding: 0.75rem;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--bg-dark);
            color: var(--white);
            font-size: 0.9rem;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 1rem;
        }
        
        .order-card {
            background: var(--card-dark);
            border-radius: 12px;
            padding: 1rem;
            border: 1px solid var(--border);
            margin-bottom: 1rem;
            text-decoration: none;
            color: inherit;
            display: block;
        }
        
        .order-card:hover {
            border-color: var(--orange);
        }
        
        .order-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        .customer-name {
            font-weight: 600;
            color: var(--white);
        }
        
        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        .status-booked { background: #1565c0; color: white; }
        .status-delivered { background: var(--yellow); color: #333; }
        .status-collected { background: var(--orange); color: white; }
        .status-complete { background: var(--green); color: white; }
        
        .order-details {
            color: var(--subtle);
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
        }
        
        .order-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .order-date {
            font-size: 0.8rem;
            color: var(--subtle);
        }
        
        .price {
            color: var(--green);
            font-weight: 600;
        }
        
        .bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: var(--card-dark);
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: space-around;
            padding: 0.75rem 0;
        }
        
        .nav-item {
            text-decoration: none;
            color: var(--subtle);
            text-align: center;
            font-size: 0.75rem;
            padding: 0.5rem;
            flex: 1;
        }
        
        .nav-item.active {
            color: var(--orange);
        }
        
        .nav-item:hover {
            color: var(--white);
        }
        
        .nav-icon { font-size: 0.75rem; font-weight: 700; color: var(--orange); letter-spacing: 1px; margin-bottom: 4px; }
        
        @media (max-width: 768px) {
            .filters {
                grid-template-columns: 1fr;
                gap: 0.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>All Orders</h1>
        <div class="filters">
            <input type="text" class="search-input" placeholder="Search customer, address, postcode..." value="{{ search }}" onchange="updateFilters()">
            <select class="filter-select" onchange="updateFilters()" id="statusFilter">
                <option value="">All Status</option>
                <option value="Booked" {{ 'selected' if status_filter == 'Booked' }}>Booked</option>
                <option value="Delivered" {{ 'selected' if status_filter == 'Delivered' }}>Delivered</option>
                <option value="Collected" {{ 'selected' if status_filter == 'Collected' }}>Collected</option>
                <option value="Complete" {{ 'selected' if status_filter == 'Complete' }}>Complete</option>
            </select>
            <select class="filter-select" onchange="updateFilters()" id="personFilter">
                <option value="">All Staff</option>
                <option value="Rob" {{ 'selected' if person_filter == 'Rob' }}>Rob</option>
                <option value="Tommy" {{ 'selected' if person_filter == 'Tommy' }}>Tommy</option>
                <option value="John" {{ 'selected' if person_filter == 'John' }}>John</option>
            </select>
        </div>
    </div>
    
    <div class="container">
        {% if orders %}
            {% for order in orders %}
            <a href="{{ url_for('order_detail', order_id=order.id) }}" class="order-card">
                <div class="order-header">
                    <div class="customer-name">{{ order.customer_name }}</div>
                    <div class="status-badge status-{{ order.status.lower() }}">{{ order.status }}</div>
                </div>
                <div class="order-details">
                    {{ order.skip_size }}  |  {{ order.job_type }}  |  {{ order.time_slot }}<br>
                    {{ order.address }}, {{ order.postcode }}
                    {% if order.company_name %} |  {{ order.company_name }}{% endif %}
                </div>
                <div class="order-meta">
                    <div>
                        <span>{{ order.assigned_to }}</span>
                        <div class="order-date">{{ order.job_date }}</div>
                    </div>
                    <div class="price">&pound;{{ "%.2f"|format(order.price_inc_vat) }}</div>
                </div>
            </a>
            {% endfor %}
        {% else %}
            <div class="order-card">
                <div style="text-align: center; color: var(--subtle);">
                    No orders found
                </div>
            </div>
        {% endif %}
    </div>
    
    <nav class="bottom-nav">
        <a href="{{ url_for('dashboard') }}" class="nav-item">
            <div class="nav-icon">HOME</div>
            Dashboard
        </a>
        <a href="{{ url_for('new_order') }}" class="nav-item">
            <div class="nav-icon">+ NEW</div>
            New Order
        </a>
        <a href="{{ url_for('order_list') }}" class="nav-item active">
            <div class="nav-icon">LIST</div>
            All Orders
        </a>
        <a href="/stats" class="nav-item"><div class="nav-icon">STATS</div>
            Stats</a>
    </nav>
    
    <script>
        function updateFilters() {
            const search = document.querySelector('.search-input').value;
            const status = document.getElementById('statusFilter').value;
            const person = document.getElementById('personFilter').value;
            
            const params = new URLSearchParams();
            if (search) params.set('search', search);
            if (status) params.set('status', status);
            if (person) params.set('assigned_to', person);
            
            window.location.href = '/orders?' + params.toString();
        }
        
        function syncSheets(event) {
            event.preventDefault();
            if (confirm('Sync all orders to Google Sheets?')) {
                fetch('/sync-sheets', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Successfully synced to Google Sheets');
                        } else {
                            alert('Sync failed: ' + data.error);
                        }
                    })
                    .catch(err => alert('Sync failed: ' + err.message));
            }
            return false;
        }
    </script>
</body>
</html>
'''

ORDER_DETAIL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="30">
    <title>Order #{{ order.id }} - Tommy's Skips</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #0f1923;
            --card-dark: #1a2836;
            --orange: #ff8c00;
            --yellow: #ffb347;
            --green: #00c853;
            --white: #ffffff;
            --subtle: #8899aa;
            --border: #2a3a4a;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg-dark);
            color: var(--white);
            min-height: 100vh;
            padding-bottom: 120px;
        }
        
        .header {
            background: var(--card-dark);
            padding: 1rem;
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header h1 {
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            color: var(--orange);
            font-size: 1.5rem;
        }
        
        .header .subtitle {
            color: var(--subtle);
            font-size: 0.9rem;
            margin-top: 0.25rem;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 1rem;
        }
        
        .detail-section {
            background: var(--card-dark);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid var(--border);
            margin-bottom: 1rem;
        }
        
        .section-title {
            font-family: 'Poppins', sans-serif;
            font-weight: 600;
            color: var(--orange);
            margin-bottom: 1rem;
            font-size: 1.1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .status-badge {
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
        }
        
        .status-booked { background: #1565c0; color: white; }
        .status-delivered { background: var(--yellow); color: #333; }
        .status-collected { background: var(--orange); color: white; }
        .status-complete { background: var(--green); color: white; }
        
        .detail-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }
        
        .detail-item {
            margin-bottom: 1rem;
        }
        
        .detail-label {
            font-weight: 500;
            color: var(--subtle);
            font-size: 0.9rem;
            margin-bottom: 0.25rem;
        }
        
        .detail-value {
            color: var(--white);
            font-size: 1rem;
        }
        
        .detail-value.price {
            color: var(--green);
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .status-buttons {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 0.5rem;
            margin-top: 1rem;
        }
        
        .status-btn {
            padding: 1rem;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--bg-dark);
            color: var(--white);
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            min-height: 56px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
        }
        
        .status-btn:hover {
            border-color: var(--orange);
        }
        
        .status-btn.current {
            background: var(--orange);
            border-color: var(--orange);
            color: var(--white);
        }
        
        .vat-breakdown {
            background: var(--bg-dark);
            border-radius: 8px;
            padding: 1rem;
            border: 1px solid var(--border);
            margin-top: 1rem;
        }
        
        .vat-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
        }
        
        .vat-total {
            border-top: 1px solid var(--border);
            padding-top: 0.5rem;
            font-weight: 600;
            color: var(--green);
        }
        
        .bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: var(--card-dark);
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: space-around;
            padding: 0.75rem 0;
        }
        
        .nav-item {
            text-decoration: none;
            color: var(--subtle);
            text-align: center;
            font-size: 0.75rem;
            padding: 0.5rem;
            flex: 1;
        }
        
        .nav-item:hover {
            color: var(--white);
        }
        
        .nav-icon { font-size: 0.75rem; font-weight: 700; color: var(--orange); letter-spacing: 1px; margin-bottom: 4px; }
        
        @media (max-width: 768px) {
            .status-buttons {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .detail-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Order #{{ order.id }}</h1>
        <div class="subtitle">{{ order.customer_name }}</div>
    </div>
    
    <div class="container">
        <!-- Order Status -->
        <div class="detail-section">
            <div class="section-title">
                Order Status
                <div class="status-badge status-{{ order.status.lower() }}">{{ order.status }}</div>
            </div>
            
            <div class="status-buttons">
                <button class="status-btn {{ 'current' if order.status == 'Booked' }}" onclick="updateStatus('Booked')">
                    " Booked
                </button>
                <button class="status-btn {{ 'current' if order.status == 'Delivered' }}" onclick="updateStatus('Delivered')">
                     Delivered
                </button>
                <button class="status-btn {{ 'current' if order.status == 'Collected' }}" onclick="updateStatus('Collected')">
                    " Collected
                </button>
                <button class="status-btn {{ 'current' if order.status == 'Complete' }}" onclick="updateStatus('Complete')">
                     Complete
                </button>
            </div>
        </div>
        
        <!-- Customer Details -->
        <div class="detail-section">
            <div class="section-title">Customer Details</div>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">Customer Name</div>
                    <div class="detail-value">{{ order.customer_name }}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Phone</div>
                    <div class="detail-value">{{ order.customer_phone }}</div>
                </div>
                {% if order.customer_email %}
                <div class="detail-item">
                    <div class="detail-label">Email</div>
                    <div class="detail-value">{{ order.customer_email }}</div>
                </div>
                {% endif %}
                <div class="detail-item">
                    <div class="detail-label">Customer Type</div>
                    <div class="detail-value">{{ order.customer_type }}</div>
                </div>
                {% if order.company_name %}
                <div class="detail-item">
                    <div class="detail-label">Company</div>
                    <div class="detail-value">{{ order.company_name }}</div>
                </div>
                {% endif %}
            </div>
        </div>
        
        <!-- Job Details -->
        <div class="detail-section">
            <div class="section-title">Job Details</div>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">Address</div>
                    <div class="detail-value">{{ order.address }}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Postcode</div>
                    <div class="detail-value">{{ order.postcode }}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Skip Size</div>
                    <div class="detail-value">{{ order.skip_size }}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Job Type</div>
                    <div class="detail-value">{{ order.job_type }}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Date</div>
                    <div class="detail-value">{{ order.job_date }}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Time Slot</div>
                    <div class="detail-value">{{ order.time_slot }}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Assigned To</div>
                    <div class="detail-value">{{ order.assigned_to }}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Waste Type</div>
                    <div class="detail-value">{{ order.waste_type }}</div>
                </div>
                {% if order.permit_needed == 'Yes' %}
                <div class="detail-item">
                    <div class="detail-label">Permit Needed</div>
                    <div class="detail-value">{{ order.permit_needed }}</div>
                </div>
                {% endif %}
                {% if order.return_date %}
                <div class="detail-item">
                    <div class="detail-label">Return Date</div>
                    <div class="detail-value">{{ order.return_date }}</div>
                </div>
                {% endif %}
            </div>
            
            {% if order.placement_instructions or order.access_issues or order.notes %}
            <div style="margin-top: 1rem;">
                {% if order.placement_instructions %}
                <div class="detail-item">
                    <div class="detail-label">Placement Instructions</div>
                    <div class="detail-value">{{ order.placement_instructions }}</div>
                </div>
                {% endif %}
                {% if order.access_issues %}
                <div class="detail-item">
                    <div class="detail-label">Access Issues</div>
                    <div class="detail-value">{{ order.access_issues }}</div>
                </div>
                {% endif %}
                {% if order.notes %}
                <div class="detail-item">
                    <div class="detail-label">Notes</div>
                    <div class="detail-value">{{ order.notes }}</div>
                </div>
                {% endif %}
            </div>
            {% endif %}
        </div>
        
        <!-- Payment Details -->
        <div class="detail-section">
            <div class="section-title">Payment Details</div>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">Payment Method</div>
                    <div class="detail-value">{{ order.payment_method }}</div>
                </div>
                {% if order.deposit_amount > 0 %}
                <div class="detail-item">
                    <div class="detail-label">Deposit Taken</div>
                    <div class="detail-value price">&pound;{{ "%.2f"|format(order.deposit_amount) }}</div>
                </div>
                {% endif %}
            </div>
            
            <div class="vat-breakdown">
                <div class="vat-row">
                    <span>Price (ex VAT):</span>
                    <span>&pound;{{ "%.2f"|format(order.price_ex_vat) }}</span>
                </div>
                <div class="vat-row">
                    <span>VAT (20%):</span>
                    <span>&pound;{{ "%.2f"|format(order.price_inc_vat - order.price_ex_vat) }}</span>
                </div>
                <div class="vat-row vat-total">
                    <span>Total (inc VAT):</span>
                    <span>&pound;{{ "%.2f"|format(order.price_inc_vat) }}</span>
                </div>
            </div>
        </div>
    </div>
    
    <nav class="bottom-nav">
        <a href="{{ url_for('dashboard') }}" class="nav-item">
            <div class="nav-icon">HOME</div>
            Dashboard
        </a>
        <a href="{{ url_for('new_order') }}" class="nav-item">
            <div class="nav-icon">+ NEW</div>
            New Order
        </a>
        <a href="{{ url_for('order_list') }}" class="nav-item">
            <div class="nav-icon">LIST</div>
            All Orders
        </a>
        <a href="/stats" class="nav-item"><div class="nav-icon">STATS</div>
            Stats</a>
    </nav>
    
    <script>
        function updateStatus(newStatus) {
            if (confirm(`Change order status to ${newStatus}?`)) {
                fetch(`/order/{{ order.id }}/status`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ status: newStatus })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('Failed to update status');
                    }
                })
                .catch(err => {
                    alert('Error updating status: ' + err.message);
                });
            }
        }
        
        function syncSheets(event) {
            event.preventDefault();
            if (confirm('Sync all orders to Google Sheets?')) {
                fetch('/sync-sheets', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Successfully synced to Google Sheets');
                        } else {
                            alert('Sync failed: ' + data.error);
                        }
                    })
                    .catch(err => alert('Sync failed: ' + err.message));
            }
            return false;
        }
    </script>
</body>
</html>
'''

# Route Optimization Template
ROUTE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Daily Routes - Tommy's Skips</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; margin: 0; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { background: #2c5aa0; color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .route-summary { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .pickup-item { background: white; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #2c5aa0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .customer-name { font-weight: bold; font-size: 1.1em; margin-bottom: 5px; }
        .address { color: #666; margin-bottom: 5px; }
        .details { font-size: 0.9em; color: #888; }
        .maps-button { background: #4285F4; color: white; padding: 15px 30px; border: none; border-radius: 25px; font-size: 1.1em; cursor: pointer; margin: 10px; text-decoration: none; display: inline-block; }
        .whatsapp-button { background: #25D366; color: white; padding: 15px 30px; border: none; border-radius: 25px; font-size: 1.1em; cursor: pointer; margin: 10px; display: inline-block; }
        .whatsapp-button.approaching { background: #FF6B35; }
        .maps-button:hover { background: #3367d6; }
        .complete-btn { background: #28a745; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; float: right; }
        .complete-btn:hover { background: #218838; }
        .date-selector { margin-bottom: 20px; }
        .date-selector input { padding: 10px; border: 2px solid #ddd; border-radius: 5px; }
        .stats { display: flex; gap: 20px; margin-top: 15px; }
        .stat { text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #2c5aa0; }
        .stat-label { color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚛 Daily Route Optimizer</h1>
            <p>Optimized pickup routes for Tommy's Skips</p>
        </div>
        
        <div class="date-selector">
            <form method="GET">
                <label for="date">Select Date:</label>
                <input type="date" name="date" value="{{ selected_date }}" onchange="this.form.submit()">
            </form>
        </div>
        
        {% if route_data.success %}
            <div class="route-summary">
                <h2>📍 Route Summary for {{ route_data.date }}</h2>
                <div class="stats">
                    <div class="stat">
                        <div class="stat-number">{{ route_data.total_pickups }}</div>
                        <div class="stat-label">Pickups</div>
                    </div>
                    {% if route_data.route_summary and route_data.route_summary.total_distance_km %}
                    <div class="stat">
                        <div class="stat-number">{{ route_data.route_summary.total_distance_km }}</div>
                        <div class="stat-label">Total KM</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{{ route_data.route_summary.total_time_hours }}</div>
                        <div class="stat-label">Hours</div>
                    </div>
                    {% endif %}
                </div>
                
                {% if route_data.google_maps_url %}
                <a href="{{ route_data.google_maps_url }}" target="_blank" class="maps-button">
                    🗺️ Open in Google Maps
                </a>
                {% endif %}
                
                <button onclick="sendETANotifications()" class="whatsapp-button">
                    📱 Send WhatsApp ETAs
                </button>
                
                <button onclick="sendApproachingAlerts()" class="whatsapp-button approaching">
                    🚛 Send "Van Approaching" Alerts
                </button>
            </div>
            
            <h3>Pickup Order:</h3>
            {% for pickup in route_data.optimized_pickups %}
            <div class="pickup-item">
                <div class="customer-name">{{ loop.index }}. {{ pickup.customer_name }}</div>
                <div class="address">📍 {{ pickup.full_address }}</div>
                <div class="details">
                    📞 {{ pickup.phone }} | 
                    🗑️ {{ pickup.skip_size }} | 
                    Status: {{ pickup.status }}
                </div>
                <button class="complete-btn" onclick="markCompleted({{ pickup.id }})">
                    ✓ Complete
                </button>
                <div style="clear: both;"></div>
            </div>
            {% endfor %}
            
        {% else %}
            <div class="route-summary">
                <h2>❌ {{ route_data.message }}</h2>
                {% if route_data.pickups %}
                <p>Showing unoptimized pickup list:</p>
                {% endif %}
            </div>
            
            {% if route_data.pickups %}
            {% for pickup in route_data.pickups %}
            <div class="pickup-item">
                <div class="customer-name">{{ loop.index }}. {{ pickup.customer_name }}</div>
                <div class="address">📍 {{ pickup.full_address }}</div>
                <div class="details">📞 {{ pickup.phone }} | 🗑️ {{ pickup.skip_size }}</div>
            </div>
            {% endfor %}
            {% endif %}
        {% endif %}
        
        <div style="margin-top: 30px; text-align: center;">
            <a href="/" style="color: #2c5aa0; text-decoration: none;">← Back to Dashboard</a>
        </div>
    </div>
    
    <script>
        function markCompleted(orderId) {
            if (confirm('Mark this pickup as completed?')) {
                fetch(`/routes/update-pickup/${orderId}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('Failed to update pickup status');
                    }
                });
            }
        }
        
        function sendETANotifications() {
            if (confirm('Send WhatsApp ETA notifications to all customers?')) {
                const btn = event.target;
                btn.textContent = '📱 Sending...';
                btn.disabled = true;
                
                fetch('/send-whatsapp-etas', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                })
                .then(response => response.json())
                .then(data => {
                    btn.disabled = false;
                    btn.textContent = '📱 Send WhatsApp ETAs';
                    
                    if (data.success) {
                        alert(`✅ WhatsApp ETAs sent successfully!\n\nSent: ${data.sent} messages\nFailed: ${data.failed} messages`);
                    } else {
                        alert(`❌ Error: ${data.message}`);
                    }
                })
                .catch(err => {
                    btn.disabled = false;
                    btn.textContent = '📱 Send WhatsApp ETAs';
                    alert('Error sending notifications: ' + err.message);
                });
            }
        }
        
        function sendApproachingAlerts() {
            if (confirm('Send "Van Approaching" alerts to customers within 15 minutes?')) {
                const btn = event.target;
                btn.textContent = '🚛 Sending...';
                btn.disabled = true;
                
                fetch('/send-approaching-alerts', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                })
                .then(response => response.json())
                .then(data => {
                    btn.disabled = false;
                    btn.textContent = '🚛 Send "Van Approaching" Alerts';
                    
                    if (data.success) {
                        if (data.sent > 0) {
                            alert(`✅ Sent "Van Approaching" alerts to ${data.sent} customers!`);
                        } else {
                            alert('ℹ️ No customers within 15 minutes of pickup.');
                        }
                    } else {
                        alert(`❌ Error: ${data.message}`);
                    }
                })
                .catch(err => {
                    btn.disabled = false;
                    btn.textContent = '🚛 Send "Van Approaching" Alerts';
                    alert('Error sending alerts: ' + err.message);
                });
            }
        }
    </script>
</body>
</html>
'''

# WhatsApp ETA Notifications
try:
    from whatsapp_notifications import WhatsAppNotifier
    WHATSAPP_ENABLED = True
except ImportError:
    WHATSAPP_ENABLED = False
    print("⚠️ WhatsApp notifications not available - install dependencies")

@app.route('/send-whatsapp-etas', methods=['POST'])
def send_whatsapp_etas():
    """Send ETA notifications to all today's pickup customers"""
    if not WHATSAPP_ENABLED:
        return jsonify({'success': False, 'message': 'WhatsApp not configured'})
    
    notifier = WhatsAppNotifier()
    result = notifier.send_daily_eta_notifications()
    return jsonify(result)

@app.route('/send-approaching-alerts', methods=['POST'])
def send_approaching_alerts():
    """Send 'van approaching' alerts for pickups within 15 minutes"""
    if not WHATSAPP_ENABLED:
        return jsonify({'success': False, 'message': 'WhatsApp not configured'})
    
    notifier = WhatsAppNotifier()
    result = notifier.send_approaching_notifications()
    return jsonify(result)

if __name__ == '__main__':
    print("Initializing Tommy's Skips database...")
    init_db()
    print("Database initialized successfully!")
    print("Starting Tommy's Skips web application...")
    print("Access the app at: http://localhost:8081")
    app.run(host='0.0.0.0', port=8081, debug=True)


