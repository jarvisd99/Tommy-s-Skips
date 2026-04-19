#!/usr/bin/env python3
"""
Test script for Tommy's Skips Route Optimizer
Creates sample orders and tests route optimization
"""
import sqlite3
import os
from datetime import datetime, timedelta
from route_optimizer import TommysRouteOptimizer

def create_test_orders():
    """Create some test orders for today"""
    conn = sqlite3.connect('tommys_skips.db')
    c = conn.cursor()
    
    # Clear existing test data
    c.execute("DELETE FROM orders WHERE customer_name LIKE 'TEST_%'")
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Sample test orders around Manchester area
    test_orders = [
        {
            'customer_name': 'TEST_Customer_1',
            'customer_phone': '07700 900123',
            'customer_email': 'test1@example.com',
            'address': '123 Main Street',
            'postcode': 'M1 4BT',
            'skip_size': '6 Yard',
            'job_date': today,
            'status': 'Delivered'
        },
        {
            'customer_name': 'TEST_Customer_2', 
            'customer_phone': '07700 900456',
            'address': '456 Oak Road',
            'postcode': 'M15 6JA',
            'skip_size': '8 Yard',
            'job_date': today,
            'status': 'Delivered'
        },
        {
            'customer_name': 'TEST_Customer_3',
            'customer_phone': '07700 900789',
            'address': '789 Church Lane',
            'postcode': 'M3 2NN',
            'skip_size': '4 Yard',
            'job_date': today,
            'status': 'Delivered'
        },
        {
            'customer_name': 'TEST_Customer_4',
            'customer_phone': '07700 900012',
            'address': '321 High Street',
            'postcode': 'M2 5RD',
            'skip_size': '6 Yard', 
            'job_date': today,
            'status': 'Delivered'
        }
    ]
    
    # Insert test orders
    for order in test_orders:
        c.execute('''
            INSERT INTO orders (
                customer_name, customer_phone, customer_email, address, postcode,
                skip_size, job_date, status, job_type, time_slot, assigned_to, 
                waste_type, permit_needed, payment_method, price_inc_vat, price_ex_vat, customer_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order['customer_name'], order['customer_phone'], order.get('customer_email'),
            order['address'], order['postcode'], order['skip_size'],
            order['job_date'], order['status'],
            'Delivery & Collection', 'Morning (9am-12pm)', 'Tommy', 'General', 'No',
            'Cash', 150.00, 125.00, 'Household'
        ))
    
    conn.commit()
    conn.close()
    
    print(f"Created {len(test_orders)} test orders for {today}")
    return len(test_orders)

def test_route_optimization():
    """Test the route optimization functionality"""
    print("\nTesting Route Optimization")
    print("=" * 40)
    
    # Create optimizer
    optimizer = TommysRouteOptimizer()
    
    # Test with today's orders
    today = datetime.now().strftime('%Y-%m-%d')
    result = optimizer.optimize_daily_route(today)
    
    print(f"\nRoute Result for {today}:")
    print(f"Success: {result['success']}")
    print(f"Total Pickups: {result.get('total_pickups', 0)}")
    
    if result['success'] and result['total_pickups'] > 0:
        print(f"\nPickup Order:")
        for i, pickup in enumerate(result.get('optimized_pickups', []), 1):
            print(f"{i}. {pickup['customer_name']} - {pickup['full_address']}")
        
        if result.get('google_maps_url'):
            print(f"\nGoogle Maps URL:")
            print(result['google_maps_url'])
        
        if 'route_summary' in result and 'total_distance_km' in result['route_summary']:
            summary = result['route_summary'] 
            print(f"\nRoute Summary:")
            print(f"Distance: {summary['total_distance_km']} km")
            print(f"Time: {summary['total_time_hours']} hours")
    
    return result

def cleanup_test_data():
    """Remove test orders"""
    conn = sqlite3.connect('tommys_skips.db')
    c = conn.cursor()
    
    c.execute("DELETE FROM orders WHERE customer_name LIKE 'TEST_%'")
    deleted = c.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"Cleaned up {deleted} test orders")

def main():
    """Run the full route optimization test"""
    print("Tommy's Skips Route Optimizer Test")
    print("=" * 50)
    
    # Check for API key
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if api_key:
        print(f"Google Maps API key found: {api_key[:20]}...")
    else:
        print("No Google Maps API key found")
        print("   Set GOOGLE_MAPS_API_KEY environment variable")
        print("   Route will work without optimization")
    
    # Create test data
    try:
        count = create_test_orders()
        
        # Test optimization
        result = test_route_optimization()
        
        # Ask about cleanup
        if input("\nClean up test data? (y/n): ").lower().startswith('y'):
            cleanup_test_data()
        else:
            print("Test orders left in database for manual testing")
            print("   View them at: http://localhost:8081/routes")
        
        print(f"\nTest completed!")
        print(f"   Route optimization: {'Working' if result['success'] else 'Failed'}")
        
        if result['success']:
            print(f"   Start the app: python app.py")
            print(f"   Visit: http://localhost:8081/routes")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()