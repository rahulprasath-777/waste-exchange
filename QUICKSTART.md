# Quick Start Guide - 5 Minutes Setup

## Prerequisites
- Python 3.7 or higher installed
- A code editor (VSCode, PyCharm, etc.)

## Step 1: Navigate to Project Directory
```bash
cd waste_exchange
```

## Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

## Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

## Step 4: Run the Application
```bash
python app.py
```

## Step 5: Open in Browser
```
http://localhost:5000
```

---

## Test the Application

### Test Credentials (Create These):

**Company 1:**
- Company Name: Green Industries
- Username: company1
- Password: pass123
- Materials: Upload Scrap Metal, Plastic Waste

**Company 2:**
- Company Name: Eco Recyclers
- Username: company2
- Password: pass456
- Materials: None initially

### Test Workflow:
1. Login as company1 → Upload materials
2. Logout
3. Login as company2 → Browse materials → Place orders
4. Logout
5. Login as company1 → Check "Received Orders" → Approve/Reject

---

## Stop the Application
Press `CTRL + C` in the terminal

## Reactivate Virtual Environment (Future Sessions)
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

## Troubleshooting Quick Fixes
- Port already in use? Change port in app.py line: `app.run(debug=True, port=5001)`
- Database error? Delete `waste_exchange.db` and restart
- Module not found? Run: `pip install -r requirements.txt` again

---

For detailed information, see README.md
