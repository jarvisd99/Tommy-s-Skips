#!/usr/bin/env python3
"""
Add demo data to Tommy's Skips app
"""

import sqlite3
from datetime import datetime, timedelta
import random

# Demo data
customers = [
    ("John Smith", "07777 123456", "john.smith@email.com", "123 Oak Street", "B12 8QR", "Household"),
    ("Sarah Jones", "07888 234567", "sarah.jones@gmail.com", "45 Mill Lane", "B15 3TG", "Household"),
    ("Mike's Builders", "07999 345678", "mike@mikesbuilders.co.uk", "78 Industrial Estate", "B21 9PL", "Commercial"),
    ("Green Gardens Ltd", "07666 456789", "info@greengardens.co.uk", "12 Garden Centre Road", "B30 1FH", "Commercial"),
    ("Mrs Thompson", "07555 567890", "mary.thompson@hotmail.com", "67 Victoria Road", "B13 4NM", "Household"),
    ("ABC Construction", "07444 678901", "contracts@abcconstruction.com", "Unit 5, Trade Park", "B33 8XY", "Commercial"),
    ("David Wilson", "07333 789012", "d.wilson@email.com", "89 Church Lane", "B14 6QP", "Household"),
    ("City Renovations", "07222 890123", "jobs@cityrenovations.co.uk", "23 High Street", "B25 7RH", "Commercial")
]

skip_sizes = ["Mini 4yd", "Midi 6yd", "Maxi 8yd"]
staff = ["Rob", "Tommy", "John"]
statuses = ["Booked", "Delivered", "Collected", "Complete"]
time_slots = ["Early Morning (7am-9am)", "Morning (9am-12pm)", "Afternoon (12pm-3pm)", "Late Afternoon (3pm-5pm)"]

def add_demo_data():
    conn = sqlite3.connect('tommys_skips_stable.db')
    c = conn.cursor()
    
    # Clear existing data
    c.execute('DELETE FROM orders')
    
    # Generate 30 demo orders over last 10 days
    for i in range(30):
        days_ago = random.randint(0, 10)
        job_date = (datetime.now() - timedelta(days=days_ago)).date().isoformat()
        
        customer = random.choice(customers)
        skip_size = random.choice(skip_sizes)
        assigned_to = random.choice(staff)
        time_slot = random.choice(time_slots)
        
        # Pricing
        prices = {"Mini 4yd": (100.00, 120.00), "Midi 6yd": (141.67, 170.00), "Maxi 8yd": (183.33, 220.00)}
        price_ex_vat, price_inc_vat = prices[skip_size]
        vat_amount = price_inc_vat - price_ex_vat
        
        # Status based on date - older orders more likely to be complete
        if days_ago > 7:
            status = "Complete"
        elif days_ago > 4:
            status = random.choice(["Collected", "Complete"])
        elif days_ago > 1:
            status = random.choice(["Delivered", "Collected"])
        else:
            status = random.choice(["Booked", "Delivered"])
        
        # Job type
        job_type = "Delivery" if status == "Booked" else "Collection" if status == "Collected" else "Exchange"
        
        c.execute('''
            INSERT INTO orders (
                customer_name, customer_phone, customer_email, address, postcode,
                skip_size, job_type, job_date, time_slot, assigned_to,
                payment_method, amount, vat_amount, total_amount, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            customer[0], customer[1], customer[2], customer[3], customer[4],
            skip_size, job_type, job_date, time_slot, assigned_to,
            "Cash" if random.random() > 0.3 else "Card",
            price_ex_vat, vat_amount, price_inc_vat, status
        ))
    
    # Add some today's jobs
    today = datetime.now().date().isoformat()
    
    for i in range(8):
        customer = random.choice(customers)
        skip_size = random.choice(skip_sizes)
        assigned_to = random.choice(staff)
        time_slot = time_slots[i % len(time_slots)]
        
        prices = {"Mini 4yd": (100.00, 120.00), "Midi 6yd": (141.67, 170.00), "Maxi 8yd": (183.33, 220.00)}
        price_ex_vat, price_inc_vat = prices[skip_size]
        vat_amount = price_inc_vat - price_ex_vat
        
        status = random.choice(["Booked", "Delivered", "Collected"])
        job_type = "Delivery" if status == "Booked" else "Collection"
        
        c.execute('''
            INSERT INTO orders (
                customer_name, customer_phone, customer_email, address, postcode,
                skip_size, job_type, job_date, time_slot, assigned_to,
                payment_method, amount, vat_amount, total_amount, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            customer[0], customer[1], customer[2], customer[3], customer[4],
            skip_size, job_type, today, time_slot, assigned_to,
            "Cash" if random.random() > 0.3 else "Card",
            price_ex_vat, vat_amount, price_inc_vat, status
        ))
    
    conn.commit()
    conn.close()
    print("Demo data added!")
    print("38 total orders")
    print("8 jobs today")
    print("Mix of household and commercial customers")
    print("Realistic pricing and status distribution")

if __name__ == "__main__":
    add_demo_data()