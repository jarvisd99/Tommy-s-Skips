#!/usr/bin/env python3
"""
Skip Inventory Tracker for Tommy's Skips
Tracks how many skips are out vs available in depot
"""

import sqlite3
from datetime import datetime

class SkipInventory:
    def __init__(self, db_path='tommys_skips.db'):
        self.db_path = db_path
        self.init_inventory_table()
    
    def init_inventory_table(self):
        """Initialize inventory tracking tables"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Skip fleet table - tracks total fleet size
        c.execute('''
            CREATE TABLE IF NOT EXISTS skip_fleet (
                size TEXT PRIMARY KEY,
                total_owned INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert default fleet sizes if not exists
        skip_sizes = ['Mini 4yd', 'Midi 6yd', 'Maxi 8yd']
        for size in skip_sizes:
            c.execute('''
                INSERT OR IGNORE INTO skip_fleet (size, total_owned) 
                VALUES (?, ?)
            ''', (size, 10))  # Default 10 skips of each size
        
        conn.commit()
        conn.close()
    
    def update_fleet_size(self, size: str, total: int):
        """Update total number of skips owned for a size"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            UPDATE skip_fleet 
            SET total_owned = ?, last_updated = CURRENT_TIMESTAMP
            WHERE size = ?
        ''', (total, size))
        
        conn.commit()
        conn.close()
    
    def get_inventory_status(self):
        """Get current inventory status - out vs available"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get total fleet
        c.execute('SELECT * FROM skip_fleet')
        fleet = {row['size']: row['total_owned'] for row in c.fetchall()}
        
        # Count skips currently out (Delivered status means skip is with customer)
        c.execute('''
            SELECT skip_size, COUNT(*) as out_count
            FROM orders 
            WHERE status IN ('Delivered', 'Booked')
            GROUP BY skip_size
        ''')
        
        out_counts = {row['skip_size']: row['out_count'] for row in c.fetchall()}
        
        # Calculate availability
        inventory = {}
        total_owned = 0
        total_out = 0
        total_available = 0
        
        for size, total in fleet.items():
            out = out_counts.get(size, 0)
            available = total - out
            
            inventory[size] = {
                'total_owned': total,
                'out_with_customers': out,
                'available_in_depot': available,
                'utilization_percent': round((out / total * 100) if total > 0 else 0, 1)
            }
            
            total_owned += total
            total_out += out
            total_available += available
        
        # Overall summary
        overall_utilization = round((total_out / total_owned * 100) if total_owned > 0 else 0, 1)
        
        conn.close()
        
        return {
            'by_size': inventory,
            'totals': {
                'total_owned': total_owned,
                'total_out': total_out,
                'total_available': total_available,
                'utilization_percent': overall_utilization
            }
        }
    
    def get_low_stock_alerts(self, threshold_percent=80):
        """Get alerts for skip sizes running low"""
        inventory = self.get_inventory_status()
        alerts = []
        
        for size, data in inventory['by_size'].items():
            if data['utilization_percent'] >= threshold_percent:
                alerts.append({
                    'size': size,
                    'available': data['available_in_depot'],
                    'utilization': data['utilization_percent'],
                    'message': f"Only {data['available_in_depot']} {size} skips available ({data['utilization_percent']}% utilization)"
                })
        
        return alerts
    
    def get_detailed_status(self):
        """Get detailed status including orders breakdown"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get orders by status and skip size
        c.execute('''
            SELECT skip_size, status, COUNT(*) as count
            FROM orders 
            GROUP BY skip_size, status
            ORDER BY skip_size, status
        ''')
        
        status_breakdown = {}
        for row in c.fetchall():
            size = row['skip_size']
            if size not in status_breakdown:
                status_breakdown[size] = {}
            status_breakdown[size][row['status']] = row['count']
        
        conn.close()
        
        return {
            'inventory': self.get_inventory_status(),
            'status_breakdown': status_breakdown,
            'alerts': self.get_low_stock_alerts()
        }

def main():
    """Test the inventory tracker"""
    tracker = SkipInventory()
    
    print("Tommy's Skips - Inventory Status")
    print("=" * 40)
    
    status = tracker.get_detailed_status()
    inventory = status['inventory']
    
    print(f"TOTAL FLEET: {inventory['totals']['total_owned']} skips")
    print(f"OUT WITH CUSTOMERS: {inventory['totals']['total_out']} skips")
    print(f"AVAILABLE IN DEPOT: {inventory['totals']['total_available']} skips")
    print(f"UTILIZATION: {inventory['totals']['utilization_percent']}%")
    print()
    
    print("BY SKIP SIZE:")
    for size, data in inventory['by_size'].items():
        print(f"  {size}:")
        print(f"    Total Owned: {data['total_owned']}")
        print(f"    Out: {data['out_with_customers']} ({data['utilization_percent']}%)")
        print(f"    Available: {data['available_in_depot']}")
        print()
    
    # Show alerts
    alerts = status['alerts']
    if alerts:
        print("LOW STOCK ALERTS:")
        for alert in alerts:
            print(f"  {alert['message']}")
    else:
        print("All skip sizes have good availability")

if __name__ == "__main__":
    main()