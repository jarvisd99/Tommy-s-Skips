#!/usr/bin/env python3
"""
WhatsApp ETA Notifications for Tommy's Skips
Sends automated pickup ETAs to customers via WhatsApp
"""
import sqlite3
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
from route_optimizer import TommysRouteOptimizer

class WhatsAppNotifier:
    def __init__(self):
        """Initialize WhatsApp API connection"""
        # Option 1: Twilio WhatsApp API (most reliable)
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN') 
        self.twilio_whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
        
        # Option 2: WhatsApp Business API (if you have it)
        self.whatsapp_api_token = os.getenv('WHATSAPP_API_TOKEN')
        self.whatsapp_phone_id = os.getenv('WHATSAPP_PHONE_ID')
        
        # Initialize route optimizer for ETAs
        self.route_optimizer = TommysRouteOptimizer()
        
    def format_phone_number(self, phone: str) -> str:
        """Format phone number for WhatsApp (UK format)"""
        # Remove all non-digits
        digits = ''.join(filter(str.isdigit, phone))
        
        # Handle UK numbers
        if digits.startswith('07'):
            # Convert 07xxx to +44 7xxx
            return f"+44{digits[1:]}"
        elif digits.startswith('447'):
            # Already in +44 format
            return f"+{digits}"
        elif len(digits) == 10:
            # Assume UK mobile without country code
            return f"+44{digits}"
        
        return f"+{digits}"  # Default fallback
    
    def send_eta_notification(self, customer_name: str, customer_phone: str, 
                            eta_minutes: int, pickup_address: str) -> bool:
        """Send ETA notification via WhatsApp"""
        
        # Format the message
        if eta_minutes <= 15:
            message = f"""🚛 *Tommy's Skips - Van Approaching!*

Hi {customer_name},

Our van will arrive for your skip pickup in approximately *{eta_minutes} minutes*.

📍 Address: {pickup_address}
⏰ ETA: {(datetime.now() + timedelta(minutes=eta_minutes)).strftime('%H:%M')}

Please ensure the skip is accessible and any vehicles are moved. Our driver will be with you shortly!

Thanks,
Tommy's Skips Team
📞 07777 752320"""
        else:
            message = f"""🚛 *Tommy's Skips - Pickup Update*

Hi {customer_name},

Your skip pickup is scheduled for today. Our van will arrive in approximately *{eta_minutes} minutes*.

📍 Address: {pickup_address}
⏰ ETA: {(datetime.now() + timedelta(minutes=eta_minutes)).strftime('%H:%M')}

We'll send another update when we're 15 minutes away.

Thanks,
Tommy's Skips Team
📞 07777 752320"""
        
        phone = self.format_phone_number(customer_phone)
        
        # Try Twilio first (most reliable)
        if self.twilio_account_sid and self.twilio_auth_token:
            return self._send_via_twilio(phone, message)
        
        # Fallback to WhatsApp Business API
        elif self.whatsapp_api_token and self.whatsapp_phone_id:
            return self._send_via_whatsapp_business(phone, message)
        
        else:
            print("❌ No WhatsApp API configured")
            print(f"📱 Would send to {phone}:")
            print(message)
            return False
    
    def _send_via_twilio(self, phone: str, message: str) -> bool:
        """Send via Twilio WhatsApp API"""
        try:
            from twilio.rest import Client
            
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            
            message = client.messages.create(
                body=message,
                from_=self.twilio_whatsapp_number,
                to=f'whatsapp:{phone}'
            )
            
            print(f"✅ WhatsApp sent via Twilio: {message.sid}")
            return True
            
        except Exception as e:
            print(f"❌ Twilio WhatsApp error: {e}")
            return False
    
    def _send_via_whatsapp_business(self, phone: str, message: str) -> bool:
        """Send via WhatsApp Business API"""
        try:
            url = f"https://graph.facebook.com/v17.0/{self.whatsapp_phone_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.whatsapp_api_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": phone.replace('+', ''),
                "type": "text",
                "text": {"body": message}
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                print(f"✅ WhatsApp sent via Business API")
                return True
            else:
                print(f"❌ WhatsApp Business API error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ WhatsApp Business API error: {e}")
            return False
    
    def calculate_route_etas(self, date: str = None) -> List[Dict]:
        """Calculate ETAs for all pickups on route"""
        route_result = self.route_optimizer.optimize_daily_route(date)
        
        if not route_result['success'] or not route_result.get('optimized_pickups'):
            return []
        
        # Start time (assume van starts at 9 AM)
        current_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        
        # If it's already past 9 AM, start from current time
        if datetime.now().hour >= 9:
            current_time = datetime.now()
        
        pickup_etas = []
        
        # Get route summary for time calculations
        route_summary = route_result.get('route_summary', {})
        total_time_minutes = route_summary.get('total_time_minutes', 0)
        
        # Estimate time per pickup (if we have route data)
        if total_time_minutes > 0 and len(route_result['optimized_pickups']) > 0:
            avg_time_per_pickup = total_time_minutes / len(route_result['optimized_pickups'])
        else:
            avg_time_per_pickup = 20  # Default 20 minutes per pickup
        
        for i, pickup in enumerate(route_result['optimized_pickups']):
            # Add travel time to current pickup
            arrival_time = current_time + timedelta(minutes=i * avg_time_per_pickup)
            eta_minutes = int((arrival_time - datetime.now()).total_seconds() / 60)
            
            pickup_etas.append({
                'order_id': pickup['id'],
                'customer_name': pickup['customer_name'],
                'phone': pickup['phone'],
                'address': pickup['full_address'],
                'eta_minutes': max(eta_minutes, 0),  # Don't go negative
                'eta_time': arrival_time,
                'pickup_order': i + 1
            })
        
        return pickup_etas
    
    def send_daily_eta_notifications(self, date: str = None) -> Dict:
        """Send ETA notifications for all today's pickups"""
        pickup_etas = self.calculate_route_etas(date)
        
        if not pickup_etas:
            return {
                'success': False,
                'message': 'No pickups found for today',
                'sent': 0,
                'failed': 0
            }
        
        sent_count = 0
        failed_count = 0
        
        for pickup in pickup_etas:
            # Only send if ETA is reasonable (within next 8 hours)
            if pickup['eta_minutes'] <= 480:
                success = self.send_eta_notification(
                    pickup['customer_name'],
                    pickup['phone'],
                    pickup['eta_minutes'],
                    pickup['address']
                )
                
                if success:
                    sent_count += 1
                    # Log the notification
                    self._log_notification(pickup['order_id'], pickup['eta_minutes'])
                else:
                    failed_count += 1
        
        return {
            'success': True,
            'message': f'ETA notifications processed',
            'sent': sent_count,
            'failed': failed_count,
            'pickups': pickup_etas
        }
    
    def send_approaching_notifications(self, threshold_minutes: int = 15) -> Dict:
        """Send 'van approaching' notifications for pickups within threshold"""
        pickup_etas = self.calculate_route_etas()
        approaching = []
        
        for pickup in pickup_etas:
            if 0 <= pickup['eta_minutes'] <= threshold_minutes:
                # Check if we haven't already sent an approaching notification
                if not self._notification_already_sent(pickup['order_id'], 'approaching'):
                    success = self.send_eta_notification(
                        pickup['customer_name'],
                        pickup['phone'],
                        pickup['eta_minutes'],
                        pickup['address']
                    )
                    
                    if success:
                        self._log_notification(pickup['order_id'], pickup['eta_minutes'], 'approaching')
                        approaching.append(pickup)
        
        return {
            'success': True,
            'sent': len(approaching),
            'approaching_pickups': approaching
        }
    
    def _log_notification(self, order_id: int, eta_minutes: int, notification_type: str = 'eta'):
        """Log sent notifications to avoid duplicates"""
        conn = sqlite3.connect('tommys_skips.db')
        c = conn.cursor()
        
        # Create notifications table if it doesn't exist
        c.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                notification_type TEXT,
                eta_minutes INTEGER,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
        ''')
        
        c.execute('''
            INSERT INTO notifications (order_id, notification_type, eta_minutes)
            VALUES (?, ?, ?)
        ''', (order_id, notification_type, eta_minutes))
        
        conn.commit()
        conn.close()
    
    def _notification_already_sent(self, order_id: int, notification_type: str) -> bool:
        """Check if notification already sent today"""
        conn = sqlite3.connect('tommys_skips.db')
        c = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        c.execute('''
            SELECT COUNT(*) FROM notifications 
            WHERE order_id = ? AND notification_type = ? 
            AND DATE(sent_at) = ?
        ''', (order_id, notification_type, today))
        
        count = c.fetchone()[0]
        conn.close()
        
        return count > 0

def main():
    """Test the WhatsApp notification system"""
    print("Tommy's Skips - WhatsApp ETA Notifications")
    print("=" * 50)
    
    notifier = WhatsAppNotifier()
    
    # Test with today's route
    result = notifier.send_daily_eta_notifications()
    
    print(f"✅ Notifications sent: {result['sent']}")
    print(f"❌ Failed: {result['failed']}")
    print(f"📱 Message: {result['message']}")
    
    if result.get('pickups'):
        print("\n📋 Pickup ETAs:")
        for pickup in result['pickups']:
            print(f"{pickup['pickup_order']}. {pickup['customer_name']} - {pickup['eta_minutes']} mins")

if __name__ == "__main__":
    main()