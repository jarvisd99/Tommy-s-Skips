# WhatsApp ETA Notifications Setup for Tommy's Skips

## 📱 Overview

Automatically send pickup ETAs to customers via WhatsApp when your van is on its way!

**Features:**
- ✅ **Automatic ETA calculation** based on optimized routes  
- ✅ **"Van approaching" alerts** when 15 minutes away
- ✅ **Professional branded messages** with Tommy's Skips branding
- ✅ **UK phone number formatting** (handles 07xxx → +44 7xxx)
- ✅ **Duplicate prevention** (won't spam customers)
- ✅ **Two API options** (Twilio or WhatsApp Business)

## 🚛 How It Works

### Route Integration:
1. **Route optimizer** calculates optimal pickup order
2. **ETA calculator** estimates arrival times for each stop  
3. **WhatsApp sender** notifies customers automatically
4. **"Approaching" alerts** sent when van is 15 mins away

### Sample Messages:

**Morning ETA (60+ minutes away):**
```
🚛 *Tommy's Skips - Pickup Update*

Hi John Smith,

Your skip pickup is scheduled for today. Our van will arrive in approximately *75 minutes*.

📍 Address: 123 Oak Street, M1 2AB
⏰ ETA: 11:15

We'll send another update when we're 15 minutes away.

Thanks,
Tommy's Skips Team
📞 07777 752320
```

**Approaching Alert (15 minutes away):**
```
🚛 *Tommy's Skips - Van Approaching!*

Hi John Smith,

Our van will arrive for your skip pickup in approximately *12 minutes*.

📍 Address: 123 Oak Street, M1 2AB  
⏰ ETA: 11:12

Please ensure the skip is accessible and any vehicles are moved. Our driver will be with you shortly!

Thanks,
Tommy's Skips Team
📞 07777 752320
```

## 🔧 Setup Options

### Option 1: Twilio WhatsApp (Recommended)

**Pros:** Most reliable, easy setup, works immediately  
**Cost:** ~£0.05 per message (roughly £2-5/month for small business)

**Setup Steps:**

1. **Sign up for Twilio:**
   - Go to: https://www.twilio.com/whatsapp
   - Create account (free trial includes $10 credit)

2. **Get WhatsApp Sandbox:**
   - In Twilio Console → Messaging → Try it out → Send a WhatsApp message
   - Follow instructions to activate sandbox
   - Note down your sandbox number (e.g. +1 415 523 8886)

3. **Get API Credentials:**
   ```bash
   Account SID: ACxxxxxxxxxxxxxxxxxxxxxxx
   Auth Token: your_auth_token_here  
   WhatsApp Number: +14155238886
   ```

4. **Add to Environment:**
   Create/update `.env` file:
   ```bash
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token_here
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
   ```

5. **Install Twilio:**
   ```bash
   pip install twilio
   ```

6. **Test Setup:**
   ```bash
   python whatsapp_notifications.py
   ```

### Option 2: WhatsApp Business API (Advanced)

**Pros:** Official WhatsApp, custom number, more features  
**Cons:** More complex setup, requires business verification  

**Setup Steps:**

1. **Apply for WhatsApp Business API:**
   - Go to: https://business.whatsapp.com/api
   - Apply with business details
   - Wait for approval (can take days/weeks)

2. **Get Credentials:**
   ```bash
   Access Token: EAAxxxxxxxxxxxxxxx
   Phone Number ID: 1234567890
   ```

3. **Add to Environment:**
   ```bash
   WHATSAPP_API_TOKEN=EAAxxxxxxxxxxxxxxx  
   WHATSAPP_PHONE_ID=1234567890
   ```

## 📋 Daily Workflow

### 1. Morning Route Planning
```bash
# Generate today's optimized route
python route_optimizer.py

# Send initial ETA notifications  
python whatsapp_notifications.py
```

### 2. Driver Updates (Manual or Automated)
- **Option A:** Driver clicks "Send ETAs" in web app
- **Option B:** Automated notifications every 30 minutes  
- **Option C:** GPS integration (advanced)

### 3. Approaching Notifications
```bash
# Send "van approaching" alerts (15 min threshold)
python -c "from whatsapp_notifications import WhatsAppNotifier; print(WhatsAppNotifier().send_approaching_notifications())"
```

## 🔗 Integration with Tommy's Skips App

### Add WhatsApp Button to Route Page

Update `app.py` route page to include:

```html
<button onclick="sendETANotifications()" class="whatsapp-button">
    📱 Send WhatsApp ETAs
</button>

<script>
function sendETANotifications() {
    fetch('/send-whatsapp-etas', {method: 'POST'})
    .then(response => response.json())  
    .then(data => {
        alert(`WhatsApp ETAs sent: ${data.sent} success, ${data.failed} failed`);
    });
}
</script>
```

### Add Flask Route

Add to `app.py`:

```python
from whatsapp_notifications import WhatsAppNotifier

@app.route('/send-whatsapp-etas', methods=['POST'])
def send_whatsapp_etas():
    notifier = WhatsAppNotifier()
    result = notifier.send_daily_eta_notifications()
    return jsonify(result)

@app.route('/send-approaching-alerts', methods=['POST'])  
def send_approaching_alerts():
    notifier = WhatsAppNotifier()
    result = notifier.send_approaching_notifications()
    return jsonify(result)
```

## 🤖 Automated Scheduling (Optional)

### Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task:
   - **Trigger:** Daily at 8:30 AM
   - **Action:** Start program
   - **Program:** `python`
   - **Arguments:** `whatsapp_notifications.py`
   - **Start in:** `C:\Users\david\.openclaw\workspace\tommys-skips`

### Linux/Mac Cron Job
```bash
# Edit crontab
crontab -e

# Add line (runs at 8:30 AM daily)
30 8 * * * cd /path/to/tommys-skips && python whatsapp_notifications.py
```

## 💰 Cost Breakdown

### Twilio WhatsApp:
- **Per message:** ~£0.05
- **Daily usage:** 10-20 messages = £0.50-£1.00
- **Monthly cost:** ~£15-30 for active business
- **ROI:** Better customer service, fewer missed pickups

### WhatsApp Business:
- **Per message:** £0.02-0.05 depending on volume
- **Setup cost:** Free (after approval)
- **Monthly cost:** ~£10-25

## 🛡️ Best Practices

### Timing:
- ✅ **Send morning ETAs** between 8-9 AM
- ✅ **Approaching alerts** when 15 minutes away  
- ❌ **Avoid** messages before 7 AM or after 6 PM
- ❌ **Don't spam** - one update per pickup max

### Content:
- ✅ **Professional tone** with Tommy's branding
- ✅ **Clear ETA times** (not just "soon")
- ✅ **Helpful instructions** (clear access, move cars)
- ✅ **Contact info** for questions

### Privacy:
- ✅ **Opt-in only** - customers consent to WhatsApp  
- ✅ **Phone validation** - check numbers are valid
- ✅ **No marketing** - pickup notifications only
- ✅ **GDPR compliance** - respect data protection

## 🔧 Troubleshooting

**"No WhatsApp API configured":**
- Check `.env` file has correct credentials
- Verify Twilio account is active
- Test API credentials in Twilio console

**"Invalid phone number":**
- Check customer phone numbers in database  
- Ensure UK format (07xxx or +44 7xxx)
- Update phone formatting in `format_phone_number()`

**"Message not delivered":**
- Customer hasn't opted into WhatsApp notifications
- Phone number is incorrect/inactive
- Twilio sandbox requires customer to join first

**"No pickups found":**
- Check orders have correct pickup dates
- Verify route optimizer is working
- Ensure orders status is "Delivered" (ready for pickup)

## 📈 Expected Benefits

**Customer Experience:**
- ✅ **Proactive communication** - customers know when van arrives
- ✅ **Reduced missed pickups** - customers are prepared  
- ✅ **Professional image** - automated, reliable updates
- ✅ **Less phone calls** - fewer "when are you coming?" calls

**Business Efficiency:**  
- ✅ **Driver efficiency** - customers ready for pickup
- ✅ **Route optimization** - combined with mapping
- ✅ **Staff time savings** - automated notifications
- ✅ **Better scheduling** - real-time ETA tracking

---

**Ready to implement?** Start with Twilio sandbox for testing, then upgrade to production when ready!