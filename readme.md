# 🥛 Dairy Manager Pro

Dairy Manager Pro is a comprehensive, multi-tenant web application designed to digitize and streamline the daily operations of milk delivery businesses (Dairies). It manages daily route sheets, customer ledgers, billing, expenses, and reporting in a unified interface.

---

## 🚀 Key Features

### 1. 🏢 Multi-Tenancy & Security
- **SaaS Architecture**: Supports multiple dairies on a single backend with strict `tenant_id` isolation.
- **Secure Authentication**: Token-based authentication (JWT-style).
- **Data Safety**: Automatic database creation and schema handling.

### 2. 🚚 Daily Route & Order Management
- Excel-like grid for fast daily quantity entry.
- Smart product columns (auto show/hide).
- Keyboard navigation (arrow keys).
- One-click **Copy Previous Day**.
- Draft vs Finalize workflow:
  - Draft: No billing impact.
  - Finalize: Locks data & updates customer dues.

### 3. 👥 Customer Management
- Live customer ledger & dues tracking.
- Customer-specific product rates.
- WhatsApp payment reminders.
- Duplicate phone number prevention.

### 4. 💰 Billing & Payments
- Cash/Online payment logging.
- PDF invoice & statement generation.
- Full payment history tracking.

### 5. 📉 Expense Manager
- Track diesel, salary, maintenance, etc.
- Expense categories.
- Staff-linked expenses.

### 6. 📊 Analytics & Reporting (`reports.html`)
- Dashboard KPIs.
- Daily sales matrix.
- Monthly customer statement.
- Day Book.
- CSV/Excel export.

---

## 🛠️ Technical Stack

### Backend (`app.py`)
- Python 3.x
- Flask
- SQLAlchemy ORM
- SQLite (Dev) / PostgreSQL (Prod)
- Token auth using `itsdangerous`
- REST JSON APIs

### Frontend (`index.html`, `reports.html`)
- Vanilla JavaScript (ES6+)
- Tailwind CSS (CDN)
- Custom reactive state store
- Client-side hash router
- Chart.js
- html2pdf.js
- FontAwesome

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.8+

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Environment Variables
Create `data.env`:
```env
SECRET_KEY=your-super-secret-key
DATABASE_URL=sqlite:///dairy_manager.db
```

### Run Application
```bash
python app.py
```

Open: http://127.0.0.1:5000  
Database auto-creates on first run.

---

## 📖 User Workflow Guide

### 1. Initial Setup
- Register New Dairy
- Add Products & Prices
- Add Staff
- Add Customers (with opening dues if any)

### 2. Daily Route Sheet
- Go to Orders & Route
- Select date
- Enter quantities or Copy Previous Day
- Save Draft
- Finalize at day end (updates dues)

### 3. Payments & Billing
- Record customer payments
- Generate PDF invoices
- Share via WhatsApp

### 4. End of Month
- Go to Reports
- Select customer & date range
- View full consumption vs payments

---

## 📂 Project Structure
```
/
├── app.py
├── index.html
├── reports.html
├── dairy_manager.db
├── data.env
└── README.md
```

---

## ⚠️ Troubleshooting

### Database Errors (500)
Use **Reset Database (Dev Only)** from login page  
⚠️ Deletes all data.

### Printing Issues
Enable **Background Graphics** in browser print settings.

---

## 📜 License
Free for personal & pilot use.  
Commercial SaaS deployment ready.

---

**Built for Indian dairy businesses 🇮🇳**
