#!/usr/bin/env python3
"""
Google Maps Route Optimizer for Tommy's Skips
Integrates with existing booking system to optimize daily routes
"""
import sqlite3
import googlemaps
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

class TommysRouteOptimizer:
    def __init__(self, api_key: str = None):
        """Initialize with Google Maps API key"""
        self.api_key = api_key or os.getenv('GOOGLE_MAPS_API_KEY')
        if self.api_key:
            self.gmaps = googlemaps.Client(key=self.api_key)
        else:
            print("No Google Maps API key provided")
            self.gmaps = None
        
        # Tommy's depot location (update this)
        self.depot_address = "Tommy's Skips Depot, Manchester"  # UPDATE WITH REAL ADDRESS
        
    def get_daily_pickups(self, date: str = None) -> List[Dict]:
        """Get all orders scheduled for pickup on a specific date"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
            
        conn = sqlite3.connect('tommys_skips.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get orders for the specified date that need pickup (delivered skips)
        c.execute('''
            SELECT id, customer_name, address, postcode, customer_phone,
                   skip_size, job_date, status
            FROM orders 
            WHERE job_date = ? AND status = 'Delivered'
            ORDER BY id
        ''', (date,))
        
        orders = []
        for row in c.fetchall():
            orders.append({
                'id': row['id'],
                'customer_name': row['customer_name'],
                'full_address': f"{row['address']}, {row['postcode']}",
                'phone': row['customer_phone'],
                'skip_size': row['skip_size'],
                'status': row['status']
            })
        
        conn.close()
        return orders
    
    def optimize_daily_route(self, date: str = None) -> Dict:
        """Optimize route for all pickups on a given date"""
        pickups = self.get_daily_pickups(date)
        
        if not pickups:
            return {
                'success': False,
                'message': f'No pickups scheduled for {date or "today"}',
                'pickups': []
            }
        
        if not self.gmaps:
            # Return basic list without optimization
            return {
                'success': False,
                'message': 'Google Maps API not available - showing unoptimized list',
                'pickups': pickups,
                'route': [p['full_address'] for p in pickups]
            }
        
        try:
            # Extract addresses for optimization
            addresses = [pickup['full_address'] for pickup in pickups]
            
            # Optimize route using Google Maps
            optimized = self._optimize_route_gmaps(addresses)
            
            if optimized:
                # Match optimized addresses back to pickup details
                optimized_pickups = []
                for addr in optimized['route'][1:-1]:  # Skip depot start/end
                    for pickup in pickups:
                        if pickup['full_address'] == addr:
                            optimized_pickups.append(pickup)
                            break
                
                return {
                    'success': True,
                    'date': date or datetime.now().strftime('%Y-%m-%d'),
                    'total_pickups': len(pickups),
                    'optimized_pickups': optimized_pickups,
                    'route_summary': optimized,
                    'google_maps_url': optimized.get('google_maps_url')
                }
            
        except Exception as e:
            print(f"Route optimization error: {e}")
            
        # Fallback to original order
        return {
            'success': True,
            'date': date or datetime.now().strftime('%Y-%m-%d'),
            'total_pickups': len(pickups),
            'optimized_pickups': pickups,
            'route_summary': {'message': 'Using original order - optimization failed'},
            'google_maps_url': self._generate_basic_maps_url([p['full_address'] for p in pickups])
        }
    
    def _optimize_route_gmaps(self, addresses: List[str]) -> Optional[Dict]:
        """Use Google Maps API to optimize route"""
        if len(addresses) > 23:  # Google Maps limit is 25 waypoints total
            print(f"⚠️ Too many addresses ({len(addresses)}), taking first 23")
            addresses = addresses[:23]
        
        all_locations = [self.depot_address] + addresses + [self.depot_address]
        
        try:
            # Get directions with waypoint optimization
            directions = self.gmaps.directions(
                origin=self.depot_address,
                destination=self.depot_address,
                waypoints=addresses,
                optimize_waypoints=True,
                mode="driving",
                departure_time=datetime.now()
            )
            
            if not directions:
                return None
                
            route = directions[0]
            optimized_order = route['waypoint_order']
            
            # Build optimized route
            optimized_addresses = [self.depot_address]
            for idx in optimized_order:
                optimized_addresses.append(addresses[idx])
            optimized_addresses.append(self.depot_address)
            
            # Calculate totals
            total_distance = sum(leg['distance']['value'] for leg in route['legs']) / 1000  # km
            total_time = sum(leg['duration']['value'] for leg in route['legs']) / 60  # minutes
            
            return {
                'route': optimized_addresses,
                'total_distance_km': round(total_distance, 1),
                'total_time_minutes': round(total_time),
                'total_time_hours': round(total_time / 60, 1),
                'waypoint_order': optimized_order,
                'google_maps_url': self._generate_optimized_maps_url(optimized_addresses)
            }
            
        except Exception as e:
            print(f"Google Maps API error: {e}")
            return None
    
    def _generate_optimized_maps_url(self, route: List[str]) -> str:
        """Generate Google Maps URL with optimized waypoints"""
        if len(route) < 2:
            return ""
            
        base_url = "https://www.google.com/maps/dir/"
        
        # Start location
        url_parts = [route[0]]
        
        # Waypoints
        for waypoint in route[1:-1]:
            url_parts.append(waypoint)
            
        # End location (if different from start)
        if route[-1] != route[0]:
            url_parts.append(route[-1])
        
        # Join with URL encoding
        encoded_route = "/".join([addr.replace(" ", "+").replace(",", "%2C") for addr in url_parts])
        return base_url + encoded_route
    
    def _generate_basic_maps_url(self, addresses: List[str]) -> str:
        """Generate basic Google Maps URL without optimization"""
        if not addresses:
            return ""
            
        base_url = "https://www.google.com/maps/dir/"
        all_stops = [self.depot_address] + addresses + [self.depot_address]
        
        encoded_route = "/".join([addr.replace(" ", "+").replace(",", "%2C") for addr in all_stops])
        return base_url + encoded_route
    
    def update_pickup_status(self, order_id: int, status: str = 'Completed'):
        """Update order status after pickup"""
        conn = sqlite3.connect('tommys_skips.db')
        c = conn.cursor()
        
        c.execute('''
            UPDATE orders 
            SET status = ?, actual_pickup_date = ?
            WHERE id = ?
        ''', (status, datetime.now().strftime('%Y-%m-%d'), order_id))
        
        conn.commit()
        conn.close()

def main():
    """Test the route optimizer"""
    print("Tommy's Skips Route Optimizer")
    print("=" * 40)
    
    # Initialize (you'll need to set GOOGLE_MAPS_API_KEY environment variable)
    optimizer = TommysRouteOptimizer()
    
    # Get today's pickups
    today = datetime.now().strftime('%Y-%m-%d')
    result = optimizer.optimize_daily_route(today)
    
    if result['success']:
        print(f"✅ Optimized route for {result['total_pickups']} pickups on {result['date']}")
        
        if 'route_summary' in result and 'total_distance_km' in result['route_summary']:
            summary = result['route_summary']
            print(f"📍 Total distance: {summary['total_distance_km']} km")
            print(f"⏱️  Estimated time: {summary['total_time_hours']} hours")
        
        print(f"\n📱 Google Maps URL:")
        print(result.get('google_maps_url', 'Not available'))
        
        print(f"\n📋 Pickup Order:")
        for i, pickup in enumerate(result['optimized_pickups'], 1):
            print(f"{i}. {pickup['customer_name']} - {pickup['full_address']} ({pickup['skip_size']})")
            
    else:
        print(f"❌ {result['message']}")

if __name__ == "__main__":
    main()