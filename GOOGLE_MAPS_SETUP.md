# Google Maps API Setup for Tommy's Skips

## 🗺️ Getting Started with Route Optimization

### Step 1: Get Google Maps API Key

1. **Go to Google Cloud Console:**
   - Visit: https://console.cloud.google.com/

2. **Create/Select Project:**
   - Create a new project or select existing one
   - Name it "Tommy's Skips Route Optimizer"

3. **Enable Required APIs:**
   - Go to "APIs & Services" → "Library"
   - Search and enable these APIs:
     - **Directions API** (for route optimization)
     - **Distance Matrix API** (for calculating distances)
     - **Places API** (for address validation)

4. **Create API Key:**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "API Key"
   - Copy the key (starts with AIza...)

5. **Secure Your API Key:**
   - Click on your API key to edit
   - Under "Application restrictions":
     - Select "HTTP referrers"
     - Add: `http://localhost:8081/*`
     - Add: `https://yourdomain.com/*` (if using custom domain)
   
   - Under "API restrictions":
     - Select "Restrict key"
     - Choose: Directions API, Distance Matrix API, Places API

### Step 2: Add API Key to Your App

Create a `.env` file in the `tommys-skips` folder:

```bash
# Create .env file
echo "GOOGLE_MAPS_API_KEY=YOUR_API_KEY_HERE" > .env
```

Or set environment variable:

**Windows:**
```cmd
set GOOGLE_MAPS_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxx
```

**Mac/Linux:**
```bash
export GOOGLE_MAPS_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxx
```

### Step 3: Install Dependencies

```bash
pip install googlemaps>=4.10.0
```

### Step 4: Test the Integration

1. **Start the app:**
   ```bash
   python app.py
   ```

2. **Visit the dashboard:**
   - Go to: http://localhost:8081
   - Click "🗺️ Daily Routes"

3. **Test with sample data:**
   - Add some orders with pickup dates
   - Visit the routes page
   - Should show optimized route with Google Maps link

## 💰 Pricing Information

**Google Maps API Costs:**
- **First 2,500 requests/month:** FREE
- **Additional requests:** ~£4-8 per 1,000 requests
- **Typical usage:** 20-50 requests per day = £5-15/month

**Cost Breakdown:**
- Daily route optimization: 1-5 requests
- Monthly cost for small business: ~£5-15
- **ROI:** Fuel savings easily cover API costs

## 🚛 Using the Route Optimizer

### Daily Workflow:

1. **Add Orders** throughout the day via the main dashboard

2. **Set Pickup Dates** when scheduling collections

3. **Generate Routes:**
   - Click "🗺️ Daily Routes" on dashboard
   - Select date (defaults to today)
   - View optimized pickup order

4. **Navigate with Google Maps:**
   - Click "🗺️ Open in Google Maps"
   - Follows optimized route automatically
   - Updates with live traffic

5. **Mark Completions:**
   - Click "✓ Complete" after each pickup
   - Updates order status automatically

### Features:

- ✅ **Automatic optimization** of pickup order
- ✅ **Real-time traffic** integration
- ✅ **Distance and time estimates**
- ✅ **One-click Google Maps navigation**
- ✅ **Mobile-friendly** interface
- ✅ **Order status tracking**

## 🔧 Advanced Configuration

### Depot Address
Update the depot address in `route_optimizer.py`:

```python
# Line 17: Update with your actual depot address
self.depot_address = "123 Your Depot Address, Manchester, UK"
```

### Route Limits
- **Maximum stops:** 23 pickups per route (Google Maps limit)
- **For more stops:** Route will optimize first 23, show remaining separately

### Troubleshooting

**"No Google Maps API key provided":**
- Check `.env` file exists with correct key
- Verify environment variable is set
- Restart the app after adding key

**"API key invalid":**
- Verify key is copied correctly
- Check API restrictions in Google Cloud Console
- Ensure required APIs are enabled

**"No pickups found":**
- Add orders with pickup dates set
- Check date selector on routes page
- Verify orders have status "Delivered" or "Pickup Requested"

## 🎯 Expected Benefits

**Time Savings:**
- 20-30% reduction in driving time
- Better route planning
- Less fuel consumption

**Customer Service:**
- More accurate pickup times
- Faster service
- Professional route optimization

**Business Efficiency:**
- Handle more pickups per day
- Reduced vehicle wear
- Better resource utilization

---

**Questions?** Check the route optimization works with a few test orders first, then scale up to daily operations.