# Dairy Manager (SaaS Backend)

A robust, multi-tenant Flask API designed to manage daily operations for dairy distribution businesses. This system handles customer management, daily order processing, billing, payments, expenses, and staff administration.

Built with **Python (Flask)** and **PostgreSQL (Supabase)**.

## 🚀 Key Features

* **🏢 Multi-Tenant Support:** Manage multiple independent dairy businesses from a single backend instance.
* **🔐 Role-Based Access Control:** Secure login for Admins and Staff (Collection Agents).
* **👥 Customer Management:** Track customer details, addresses, and individual dues.
* **🥛 Product Management:** customized product lists with dynamic pricing.
* **📅 Daily Orders:** Efficient daily order entry with "Draft" and "Finalized" statuses.
* **💰 Financials:** Record payments, track customer balances, and manage business expenses.
* **🔄 Auto-Healing Database:** Automatically seeds default products for new tenants upon first login.
* **📊 Reporting:** API endpoints for syncing data and generating reports.

## 🛠️ Tech Stack

* **Language:** Python 3.x
* **Framework:** Flask
* **ORM:** SQLAlchemy
* **Database:** PostgreSQL (via Supabase)
* **Authentication:** Werkzeug Security & ItsDangerous (Token-based)
* **CORS:** Flask-CORS enabled for frontend integration

## ⚙️ Setup & Installation

### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/dairy-manager-backend.git](https://github.com/your-username/dairy-manager-backend.git)
cd dairy-manager-backend

```

### 2. Create a Virtual Environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

```

### 3. Install Dependencies

Create a `requirements.txt` file (if you haven't already) with the following content, then install:

```bash
pip install flask flask-sqlalchemy flask-cors psycopg2-binary python-dotenv

```

### 4. Environment Configuration

Create a `.env` file in the root directory and add your credentials:

```ini
SECRET_KEY=your_secure_random_key_here
DATABASE_URL=postgresql://user:password@host:port/database

```

> **Note:** If using Supabase, use the "Session" connection string (port 5432).

## 🗄️ Database Setup

The application uses SQLAlchemy. When you run the app for the first time, it will automatically create the necessary tables (`dairy_tenant`, `dairy_user`, `customer`, `order`, etc.).

### Creating a Tenant (Manual SQL)

Since public registration is disabled for security, you must manually insert new tenants and admin users directly into your database (e.g., Supabase SQL Editor).

1. **Generate a Password Hash:**
Run this python one-liner to get your hashed password:
```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your_password'))"

```


2. **Run SQL Commands:**
```sql
-- 1. Create Tenant
INSERT INTO dairy_tenant (id, name, location_code, location_seq, location_name, created_at)
VALUES ('HYD01', 'My Dairy Business', 'HYD', 1, 'Hyderabad', NOW());

-- 2. Create Admin User (Paste hash from step 1)
INSERT INTO dairy_user (username, password, role, tenant_id)
VALUES ('admin_user', 'scrypt:32768:8:1$....', 'admin', 'HYD01');

```


3. **Auto-Setup:**
Log in via the frontend/API. The system will detect the new tenant and automatically populate the default product list.

## 🏃‍♂️ Running the Application

```bash
python app.py

```

The server will start on `http://127.0.0.1:5000`.

## 📡 API Endpoints Overview

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/login` | Authenticate and retrieve token |
| `GET` | `/api/sync` | Get all master data (customers, products, etc.) |
| `POST` | `/api/orders/save` | Save or update daily orders |
| `POST` | `/api/sheets/finalize` | Finalize orders for the day and update dues |
| `POST` | `/api/payments` | Record customer payments |
| `GET` | `/api/dashboard` | Get revenue and due statistics |

## 📄 License

This project is for private use or strictly for educational purposes.

```

```