# Tommy's Skips - Skip Hire Management App

A professional web application for managing skip hire orders for Tommy's Skips business.

## Features

- **Quick Order Entry** - Minimal typing, big tap buttons for fast mobile entry
- **Daily Schedule** - Today's jobs at a glance with summary statistics
- **🗺️ Route Optimization** - Google Maps integration for optimized pickup routes
- **Order Tracking** - Status flow: Booked → Delivered → Collected → Complete
- **Mobile-First Design** - Works perfectly on phones and tablets
- **VAT Management** - Automatic VAT calculations and breakdown
- **Google Sheets Integration** - Sync all orders to Google Sheets (placeholder ready)
- **Professional UI** - Dark theme matching Tommy's Skips branding

## Quick Start

1. **Install Python** (if not already installed)
2. **Install dependencies**:
   ```bash
   pip install Flask googlemaps
   ```
   
3. **Set up Google Maps** (for route optimization):
   ```bash
   # Get API key from Google Cloud Console
   export GOOGLE_MAPS_API_KEY=your_api_key_here
   ```
   See [GOOGLE_MAPS_SETUP.md](GOOGLE_MAPS_SETUP.md) for detailed instructions.
3. **Run the application**:
   ```bash
   python app.py
   ```
4. **Open in browser**: http://localhost:8081

## Usage

### Dashboard (/)
- View today's jobs and revenue summary
- Quick stats by person and status
- Large "Add New Order" button for fast access

### New Order (/new)
- **Fast Entry**: Main form takes 30 seconds - name, address, skip size, date, time, person, payment
- **More Details**: Collapsible section for additional info when needed
- Smart defaults and validation

### Order List (/orders)
- View all orders with search and filters
- Filter by status (Booked/Delivered/Collected/Complete)
- Filter by assigned person (Rob/Tommy/John)

### Order Detail (/order/<id>)
- Complete order information
- One-tap status changes
- VAT breakdown display
- Customer and job details

### Route Optimization (/routes)
- **Daily route planning** with Google Maps integration
- **Automatic optimization** of pickup order to minimize driving time
- **One-click navigation** - opens optimized route in Google Maps
- **Real-time traffic** integration for accurate time estimates
- **Mobile-friendly** interface for drivers
- **Order completion tracking** - mark pickups complete on-the-go

**Route Features:**
- Optimizes up to 23 pickups per route
- Calculates total distance and time
- Shows customer details and skip sizes
- Integrates with existing order management

## Business Details

**Company**: Tommy's Skips  
**Tagline**: "Speed & Reliability You Can Trust"  
**Phone**: 07777 752320  
**Staff**: Rob, Tommy, John  

### Skip Sizes & Pricing (inc VAT)
- **Mini 4yd**: £120.00 (£100.00 ex VAT)
- **Midi 6yd**: £170.00 (£141.67 ex VAT)  
- **Maxi 8yd**: £220.00 (£183.33 ex VAT)

### Time Slots
- Early Morning (7am-9am)
- Morning (9am-12pm)
- Afternoon (12pm-3pm)
- Late Afternoon (3pm-5pm)

## Database

SQLite database (`tommys_skips.db`) stores all orders with complete audit trail.

**Order Fields**:
- Customer info (name, phone, email, address, postcode)
- Business details (company name, customer type)
- Skip details (size, waste type, permit required)
- Job details (type, date, time, assigned person, placement, access)
- Payment (method, amount, deposit, VAT breakdown)
- Status tracking and timestamps

## Google Sheets Integration

The app includes Google Sheets sync functionality (currently placeholder). To enable:

1. Set up Google Sheets API credentials
2. Install gspread: `pip install gspread`
3. Configure service account in the sync function
4. Update the `sync_to_google_sheets()` function

## Mobile Experience

Optimized for mobile use with:
- Big 56px+ tap targets
- Pull-to-refresh support
- Touch-friendly navigation
- Fast form completion
- Offline-capable design

## Security

- No external API calls required for basic functionality
- Local SQLite database
- Session management with Flask
- Input validation and sanitization

## Support

Built for Tommy's Skips team (Rob, Tommy, John) - designed for speed and reliability in real-world skip hire operations.

**Port**: 8081 (to avoid conflicts with other services on 8080)