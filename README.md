# Industrial Waste Exchange Platform

A simple Flask-based web application for buying and selling industrial waste materials between companies.

## Features

✅ **User Management**
- Company registration with unique usernames and emails
- Secure login/logout system
- Password hashing for security

✅ **Waste Material Management**
- Upload waste materials with details (name, description, price, quantity)
- View all available materials from other companies
- View your own uploaded materials
- Delete materials

✅ **Ordering System**
- Browse available materials
- Place orders with quantity selection
- Real-time price calculation
- Order status management (pending, approved, rejected, completed)
- Track orders placed and received

✅ **Database**
- SQLite database for data persistence
- Three main tables: users, waste_materials, orders

## Project Structure

```
waste_exchange/
├── app.py                      # Main Flask application
├── waste_exchange.db          # SQLite database (auto-created)
├── requirements.txt           # Python dependencies
└── templates/
    ├── base.html              # Base template with navigation
    ├── index.html             # Home page
    ├── register.html          # User registration
    ├── login.html             # User login
    ├── dashboard.html         # Browse all materials
    ├── my_materials.html      # User's own materials
    ├── upload_material.html    # Upload form
    ├── view_material.html      # Material details
    ├── order_material.html     # Order placement form
    ├── my_orders.html          # Orders placed by user
    ├── received_orders.html    # Orders received for user's materials
    ├── 404.html               # Not found error page
    └── 500.html               # Server error page
```

## Installation & Setup

### Step 1: Prerequisites
Make sure you have Python 3.7+ installed on your system.

```bash
python --version
```

### Step 2: Clone/Create Project Folder
```bash
mkdir waste_exchange
cd waste_exchange
```

### Step 3: Create Virtual Environment (Optional but Recommended)

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

The requirements include:
- Flask: Web framework
- Werkzeug: Security utilities (password hashing)

### Step 5: Run the Application
```bash
python app.py
```

You should see output like:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

### Step 6: Access the Application
Open your web browser and navigate to:
```
http://localhost:5000
```

## How to Use

### First Time Users

1. **Register a Company Account**
   - Click "Register" in the navigation
   - Enter company name, username, email, and password
   - Click "Register"

2. **Login**
   - Click "Login" in the navigation
   - Enter username and password
   - Click "Login"

### Managing Materials

3. **Upload Waste Materials**
   - Click "Upload" in navigation (after login)
   - Fill in material details:
     - Material Name (required)
     - Description (optional)
     - Price per Unit (required)
     - Unit type (kg, ton, liter, piece, box, bag)
     - Quantity Available (required)
   - Click "Upload Material"

4. **View Your Materials**
   - Click "My Materials" in navigation
   - See all your uploaded materials
   - Delete materials as needed

### Browsing and Ordering

5. **Browse All Materials**
   - Click "Browse" in navigation
   - See all materials from other companies
   - Click "View Details" for more information
   - Click "Order" to place an order

6. **Place an Order**
   - Select quantity (must be ≤ available quantity)
   - System shows real-time price calculation
   - Click "Place Order"
   - Order status starts as "Pending"

### Order Management

7. **Track Your Orders (Placed)**
   - Click "My Orders" in navigation
   - See all orders you've placed
   - View order status (pending, approved, rejected, completed)

8. **Manage Orders (Received)**
   - Click "Received Orders" in navigation
   - See all orders for your materials
   - Approve or Reject pending orders
   - Mark approved orders as completed

## Database Schema

### Users Table
```
- id (Primary Key)
- username (Unique)
- email (Unique)
- password_hash
- company_name
- created_at (Timestamp)
```

### Waste Materials Table
```
- id (Primary Key)
- name
- description
- price_per_unit
- quantity
- unit
- user_id (Foreign Key)
- company_name
- created_at (Timestamp)
```

### Orders Table
```
- id (Primary Key)
- buyer_id (Foreign Key)
- material_id (Foreign Key)
- quantity
- total_price
- status (pending, approved, rejected, completed)
- created_at (Timestamp)
```

## Features Explained

### Authentication
- Passwords are hashed using Werkzeug's security functions
- Session management for user authentication
- Login decorator prevents unauthorized access

### Material Management
- Each material is linked to the uploading user
- Quantity automatically updates when orders are placed
- Users can only delete their own materials

### Order Workflow
1. Buyer places order → Status: "Pending"
2. Seller reviews order
3. Seller approves/rejects order
4. If approved, Seller marks as completed
5. Quantity is automatically reduced when order is placed

### Security Features
- Password hashing (SHA256)
- Session-based authentication
- User ownership verification for protected actions
- SQL injection prevention using parameterized queries

## Cloud & Production Deployment (Render + PostgreSQL + Cloudinary)

This platform supports **persistent PostgreSQL storage** on Render and **Cloudinary** cloud image hosting so your users, passwords, and images are permanently saved across restarts and redeploys.

### 1. Render Deployment
- Render automatically provisions the PostgreSQL database specified in `render.yaml`.
- The `DATABASE_URL` environment variable is linked automatically.

### 2. Free Cloudinary Setup for Photos
1. Create a free account at [cloudinary.com](https://cloudinary.com).
2. Go to your Cloudinary Dashboard and copy your **Cloud Name**, **API Key**, and **API Secret** (or **API Environment variable URL** `CLOUDINARY_URL`).
3. In your Render Dashboard (under **Environment Variables** for your web service), add:
   - `CLOUDINARY_CLOUD_NAME` = your_cloud_name
   - `CLOUDINARY_API_KEY` = your_api_key
   - `CLOUDINARY_API_SECRET` = your_api_secret
   *(or simply add `CLOUDINARY_URL = cloudinary://<api_key>:<api_secret>@<cloud_name>`)*

When running locally without credentials, the platform seamlessly falls back to SQLite and local image storage!

## Configuration

You can modify the following in `app.py`:

```python
# Change the secret key (IMPORTANT for production)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'

# Port and debug mode
app.run(debug=True, port=5000)
```

## Troubleshooting

### Database Issues
If you encounter database errors, delete `waste_exchange.db` and restart the app:
```bash
rm waste_exchange.db
python app.py
```

### Port Already in Use
If port 5000 is busy, change it in `app.py`:
```python
app.run(debug=True, port=5001)  # Use 5001 instead
```

### Module Not Found Errors
Make sure you've installed requirements:
```bash
pip install -r requirements.txt
```

### Virtual Environment Issues
Deactivate and reactivate:
```bash
deactivate
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

## Demo Data

To add test data quickly, use the web interface:

1. Register 2-3 companies
2. Login to each and upload different materials
3. Switch to another company and place orders
4. Manage orders from both perspectives

## Example Usage Scenario

**Company A:**
1. Registers as "Green Industries"
2. Uploads 500 kg of Scrap Aluminum at ₹50/kg
3. Uploads 1000 kg of Plastic Waste at ₹30/kg

**Company B:**
1. Registers as "Eco Recyclers"
2. Browses materials
3. Orders 200 kg of Scrap Aluminum from Green Industries
4. Orders 500 kg of Plastic Waste from Green Industries

**Back to Company A:**
1. Checks "Received Orders"
2. Approves both orders
3. Marks orders as completed

**Back to Company B:**
1. Checks "My Orders"
2. Sees order statuses change to "approved" then "completed"

## Future Enhancements

- Email notifications for order updates
- Payment integration (Razorpay, Stripe)
- Admin dashboard
- Advanced search and filters
- User ratings and reviews
- Material categories and tags
- Bulk upload functionality
- API endpoints
- Mobile app
- Waste material pricing history

## Support

For issues or questions, check:
1. Make sure all dependencies are installed
2. Verify Python version is 3.7+
3. Check that port 5000 is available
4. Ensure SQLite is available on your system

## License

This project is open source and available for educational and commercial use.

---

**Happy Trading! ♻️**
