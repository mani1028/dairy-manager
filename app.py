import os
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, jsonify, request, send_file, g
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, and_
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

# --- CONFIGURATION ---
load_dotenv('data.env') 

app = Flask(__name__)
# PRODUCTION NOTE: Change this key in your environment variables for security
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-to-a-secure-random-key-in-production')
CORS(app) 

# --- DATABASE SETUP (FIXED) ---
# 1. Get the URL from environment (Render sets this automatically)
database_url = os.environ.get('DATABASE_URL')

# 2. Fallback for local testing (Your Supabase URL)
if not database_url:
    database_url = "postgresql://postgres.tkgnfijktdmvgvsdbneq:IKyNw6s0HdwGpKQ1@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

# 3. Fix the 'postgres://' vs 'postgresql://' issue
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

DEFAULT_PRODUCTS = [
    {'code': 'p1', 'name': 'FCM 1L', 'price': 70, 'unit': 'Pkt'},
    {'code': 'p2', 'name': 'FCM 500ml', 'price': 35, 'unit': 'Pkt'},
    {'code': 'p3', 'name': 'STD 1L', 'price': 65, 'unit': 'Pkt'},
    {'code': 'p4', 'name': 'STD 500ml', 'price': 33, 'unit': 'Pkt'},
    {'code': 'p5', 'name': 'TM 1L', 'price': 60, 'unit': 'Pkt'},
    {'code': 'p6', 'name': 'TM 500ml', 'price': 30, 'unit': 'Pkt'},
    {'code': 'p7', 'name': 'T-SPL 500ml', 'price': 32, 'unit': 'Pkt'},
    {'code': 'p8', 'name': 'GOLD Small', 'price': 10, 'unit': 'Pkt'},
    {'code': 'p10', 'name': 'Curd 500gm', 'price': 25, 'unit': 'Pkt'},
    {'code': 'p11', 'name': 'DTM 900gm', 'price': 50, 'unit': 'Kg'},
    {'code': 'p12', 'name': 'Skim 10kg', 'price': 450, 'unit': 'bkt'},
    {'code': 'p13', 'name': 'DTM 10kg', 'price': 500, 'unit': 'bkt'},
    {'code': 'p14', 'name': 'TM 10kg', 'price': 300, 'unit': 'bkt'},
    {'code': 'p15', 'name': '5kg BKT', 'price': 300, 'unit': 'bkt'},
    {'code': 'p16', 'name': 'Paneer 1kg', 'price': 350, 'unit': 'pkt'},
    {'code': 'p17', 'name': 'Paneer 500gm', 'price': 300, 'unit': 'pkt'},
    {'code': 'p18', 'name': '20kg can', 'price': 300, 'unit': 'bkt'},
    {'code': 'p19', 'name': 'COWA 500gm', 'price': 300, 'unit': 'kg'},
    {'code': 'p20', 'name': 'Cowa 1kg', 'price': 300, 'unit': 'kg'},
    {'code': 'p21', 'name': 'Badam Milk', 'price': 300, 'unit': 'pkt'},
    {'code': 'p24', 'name': 'Butter', 'price': 500, 'unit': 'Kg'},
    {'code': 'p25', 'name': 'Ghee', 'price': 600, 'unit': 'Kg'},
]

# --- MULTI-TENANT MODELS ---

class DairyTenant(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location_code = db.Column(db.String(10), nullable=False)
    location_seq = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DairyUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='admin')
    tenant_id = db.Column(db.String(50), db.ForeignKey('dairy_tenant.id'), nullable=False)

# --- APP MODELS (TENANT SCOPED) ---

class Employee(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('dairy_tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(50))

    def to_dict(self):
        return {"id": self.id, "name": self.name, "phone": self.phone, "role": self.role}

class Product(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('dairy_tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "price": self.price, "unit": self.unit, "isActive": self.is_active}

class Customer(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('dairy_tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    dues = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='Active')
    rates = db.relationship('CustomerRate', backref='customer', cascade="all, delete-orphan")

    def to_dict(self):
        custom_rates = {r.product_id: r.rate for r in self.rates}
        return {
            "id": self.id, "name": self.name, "phone": self.phone, 
            "address": self.address, "dues": self.dues, 
            "status": self.status, "customRates": custom_rates
        }

class CustomerRate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('dairy_tenant.id'), nullable=False)
    customer_id = db.Column(db.String(50), db.ForeignKey('customer.id'), nullable=False)
    product_id = db.Column(db.String(50), nullable=False)
    rate = db.Column(db.Float, nullable=False)

class Order(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('dairy_tenant.id'), nullable=False)
    customer_id = db.Column(db.String(50), db.ForeignKey('customer.id'))
    customer_name = db.Column(db.String(100)) 
    date = db.Column(db.String(20), nullable=False) 
    status = db.Column(db.String(20)) 
    total = db.Column(db.Float, default=0.0)
    items_json = db.Column(db.Text, default='[]') 

    def to_dict(self):
        items_list = []
        if self.items_json:
            try:
                items_list = json.loads(self.items_json)
            except:
                items_list = []
        
        formatted_items = []
        for i in items_list:
            formatted_items.append({
                "id": i.get('productId') or i.get('id'),
                "name": i.get('name'),
                "quantity": i.get('quantity'),
                "price": i.get('price')
            })

        return {
            "id": self.id, "customerId": self.customer_id, "customerName": self.customer_name,
            "date": self.date, "status": self.status, "total": self.total,
            "items": formatted_items
        }

class Payment(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('dairy_tenant.id'), nullable=False)
    customer_id = db.Column(db.String(50), db.ForeignKey('customer.id'))
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(20))
    collected_by = db.Column(db.String(100))
    note = db.Column(db.String(200))

    def to_dict(self):
        return {
            "id": self.id, "customerId": self.customer_id, "amount": self.amount,
            "date": self.date, "collectedBy": self.collected_by, "note": self.note
        }

class Expense(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('dairy_tenant.id'), nullable=False)
    title = db.Column(db.String(200))
    amount = db.Column(db.Float)
    category = db.Column(db.String(50))
    date = db.Column(db.String(20))
    employee_id = db.Column(db.String(50)) 

    def to_dict(self):
        return {
            "id": self.id, "title": self.title, "amount": self.amount,
            "category": self.category, "date": self.date, "employeeId": self.employee_id
        }

# --- HELPERS & MIDDLEWARE ---

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Missing token'}), 401
        try:
            token = auth_header.split(" ")[1]
            data = serializer.loads(token, max_age=86400) # Valid for 1 day
            g.tenant_id = data['tenant_id']
            g.user_id = data['user_id']
        except (SignatureExpired, BadSignature, IndexError):
            return jsonify({'error': 'Invalid or expired token'}), 401
        return f(*args, **kwargs)
    return decorated

# --- ROUTES ---

@app.route('/')
def home():
    return send_file('index.html')

@app.route('/index.html')
def home_explicit():
    return send_file('index.html')

@app.route('/reports.html')
@app.route('/reports')
def reports_page():
    return send_file('reports.html')

# --- AUTHENTICATION ---

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = DairyUser.query.filter_by(username=data.get('username')).first()
    
    if user and user.password == data.get('password'):
        token = serializer.dumps({'user_id': user.id, 'tenant_id': user.tenant_id})
        tenant = DairyTenant.query.get(user.tenant_id)
        return jsonify({
            "token": token,
            "tenant_id": user.tenant_id,
            "business_name": tenant.name,
            "role": user.role
        })
        
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/sync', methods=['GET'])
@require_auth
def sync_data():
    try:
        tid = g.tenant_id
        customers = [c.to_dict() for c in Customer.query.filter_by(tenant_id=tid).all()]
        products = [p.to_dict() for p in Product.query.filter_by(tenant_id=tid).all()]
        employees = [e.to_dict() for e in Employee.query.filter_by(tenant_id=tid).all()]
        recent_payments = [p.to_dict() for p in Payment.query.filter_by(tenant_id=tid).order_by(Payment.date.desc()).limit(1000).all()]
        expenses = [e.to_dict() for e in Expense.query.filter_by(tenant_id=tid).order_by(Expense.date.desc()).limit(1000).all()]
        
        year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        recent_orders = [o.to_dict() for o in Order.query.filter(and_(Order.tenant_id == tid, Order.date >= year_ago)).all()]
        
        return jsonify({
            "customers": customers, "products": products, "employees": employees,
            "payments": recent_payments, "expenses": expenses, "orders": recent_orders
        })
    except OperationalError:
        return jsonify({"error": "Database error."}), 500

# --- CORE API ROUTES ---

@app.route('/api/customers', methods=['POST'])
@require_auth
def add_customer():
    data = request.json
    tid = g.tenant_id
    if Customer.query.filter_by(tenant_id=tid, phone=data['phone']).first():
        return jsonify({"error": "Phone number already exists"}), 400
    count = Customer.query.filter_by(tenant_id=tid).count()
    new_id = f"{tid}C{count + 1:03d}"
    c = Customer(id=new_id, tenant_id=tid, name=data['name'], phone=data['phone'], address=data.get('address'), dues=float(data.get('dues', 0)))
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict())

@app.route('/api/customers/<id>', methods=['PUT', 'DELETE'])
@require_auth
def mod_customer(id):
    c = Customer.query.filter_by(id=id, tenant_id=g.tenant_id).first()
    if not c: return jsonify({"error": "Not found"}), 404
    
    if request.method == 'DELETE':
        db.session.delete(c)
    else:
        data = request.json
        c.name = data['name']
        c.phone = data['phone']
        c.address = data.get('address')
        if 'dues' in data: c.dues = float(data['dues'])
    
    db.session.commit()
    return jsonify(c.to_dict() if request.method == 'PUT' else {"message": "Deleted"})

@app.route('/api/customers/<cid>/rates', methods=['POST'])
@require_auth
def update_rates(cid):
    data = request.json
    tid = g.tenant_id
    rates_map = data.get('rates', {})
    scope = data.get('scope', 'future')

    CustomerRate.query.filter_by(customer_id=cid, tenant_id=tid).delete()
    for pid, rate in rates_map.items():
        db.session.add(CustomerRate(tenant_id=tid, customer_id=cid, product_id=pid, rate=rate))
    
    updated_draft = False
    if scope == 'today':
        today = datetime.now().strftime('%Y-%m-%d')
        draft_order = Order.query.filter_by(customer_id=cid, date=today, status='draft', tenant_id=tid).first()
        if draft_order:
            items = []
            if draft_order.items_json:
                items = json.loads(draft_order.items_json)
            
            new_total = 0
            for item in items:
                pid = item.get('productId') or item.get('id')
                prod = Product.query.filter_by(id=pid, tenant_id=tid).first()
                if prod:
                    new_rate = rates_map.get(prod.id, prod.price)
                    item['price'] = new_rate
                    new_total += item['quantity'] * new_rate
            
            draft_order.items_json = json.dumps(items)
            draft_order.total = new_total
            updated_draft = True

    db.session.commit()
    return jsonify({"message": "Rates updated", "draft_updated": updated_draft})

@app.route('/api/sheets/finalize', methods=['POST'])
@require_auth
def finalize_sheet():
    data = request.json
    date_str = data.get('date')
    tid = g.tenant_id
    
    if not date_str: return jsonify({"error": "Date required"}), 400

    orders = Order.query.filter_by(date=date_str, tenant_id=tid).all()
    count = 0
    
    for o in orders:
        if o.status != 'finalized':
            cust = Customer.query.filter_by(id=o.customer_id, tenant_id=tid).first()
            if cust:
                cust.dues += o.total
            o.status = 'finalized'
            count += 1
            
    db.session.commit()
    return jsonify({"success": True, "message": f"Finalized {count} orders for {date_str}"})

@app.route('/api/orders', methods=['GET'])
@require_auth
def get_orders():
    date_str = request.args.get('date')
    orders = Order.query.filter_by(date=date_str, tenant_id=g.tenant_id).all()
    return jsonify([o.to_dict() for o in orders])

@app.route('/api/orders/save', methods=['POST'])
@require_auth
def save_orders():
    data = request.json
    tid = g.tenant_id
    date_str = data['date']
    incoming_orders = data['orders']
    count = 0
    
    for ord_data in incoming_orders:
        customer_id = ord_data['customerId']
        cust = Customer.query.filter_by(id=customer_id, tenant_id=tid).first()
        if not cust: continue

        existing = Order.query.filter_by(customer_id=customer_id, date=date_str, tenant_id=tid).first()
        
        if existing and existing.status == 'finalized':
            cust.dues -= existing.total
        
        items_json_str = json.dumps(ord_data['items'])

        if existing:
            existing.total = ord_data['total']
            existing.status = ord_data['status']
            existing.customer_name = ord_data['customerName']
            existing.items_json = items_json_str 
        else:
            new_order = Order(
                id=ord_data['id'], tenant_id=tid, customer_id=customer_id, 
                customer_name=ord_data['customerName'], date=date_str, 
                status=ord_data['status'], total=ord_data['total'],
                items_json=items_json_str 
            )
            db.session.add(new_order)
        
        if ord_data['status'] == 'finalized':
            cust.dues += ord_data['total']
        count += 1
        
    db.session.commit()
    return jsonify({"message": f"Processed {count} orders. Ledgers updated."})

@app.route('/api/payments', methods=['POST'])
@require_auth
def add_payment():
    data = request.json
    tid = g.tenant_id
    cust = Customer.query.filter_by(id=data['customerId'], tenant_id=tid).first()
    if not cust: return jsonify({"error": "Customer not found"}), 404

    new_pay = Payment(
        id=str(int(datetime.now().timestamp() * 1000)), 
        tenant_id=tid, customer_id=data['customerId'],
        amount=data['amount'], date=data['date'], 
        collected_by=data.get('collectedBy'), note=data.get('note')
    )
    cust.dues -= float(data['amount'])
    db.session.add(new_pay)
    db.session.commit()
    return jsonify({"message": "Payment recorded", "new_dues": cust.dues})

@app.route('/api/expenses', methods=['GET', 'POST'])
@require_auth
def manage_expenses():
    tid = g.tenant_id
    if request.method == 'POST':
        data = request.json
        exp = Expense(
            id=str(int(datetime.now().timestamp())), tenant_id=tid,
            title=data['title'], amount=data['amount'],
            category=data['category'], date=data['date'], employee_id=data.get('employeeId')
        )
        db.session.add(exp)
        db.session.commit()
        return jsonify(exp.to_dict())
    else:
        start = request.args.get('startDate')
        end = request.args.get('endDate')
        emp_id = request.args.get('employeeId')
        query = Expense.query.filter_by(tenant_id=tid)
        if start and end: query = query.filter(and_(Expense.date >= start, Expense.date <= end))
        if emp_id: query = query.filter_by(employee_id=emp_id)
        exps = query.order_by(Expense.date.desc()).all()
        return jsonify([e.to_dict() for e in exps])

@app.route('/api/reports/data', methods=['GET'])
@require_auth
def get_report_data():
    tid = g.tenant_id
    start = request.args.get('start')
    end = request.args.get('end')
    if not start or not end: return jsonify({"error": "Start and End dates required"}), 400

    orders = Order.query.filter(and_(Order.tenant_id == tid, Order.date >= start, Order.date <= end)).all()
    payments = Payment.query.filter(and_(Payment.tenant_id == tid, Payment.date >= start, Payment.date <= end)).all()
    expenses = Expense.query.filter(and_(Expense.tenant_id == tid, Expense.date >= start, Expense.date <= end)).all()

    return jsonify({
        "orders": [o.to_dict() for o in orders],
        "payments": [p.to_dict() for p in payments],
        "expenses": [e.to_dict() for e in expenses]
    })

@app.route('/api/dashboard', methods=['GET'])
@require_auth
def dashboard_stats():
    tid = g.tenant_id
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    live_total_dues = db.session.query(func.sum(Customer.dues)).filter_by(tenant_id=tid).scalar() or 0
    active_customers = Customer.query.filter_by(tenant_id=tid, status='Active').count()

    future_orders = Order.query.filter(and_(Order.tenant_id == tid, Order.date > date_str, Order.status == 'finalized')).all()
    future_payments = Payment.query.filter(and_(Payment.tenant_id == tid, Payment.date > date_str)).all()
    
    future_sales_sum = sum(o.total for o in future_orders)
    future_payments_sum = sum(p.amount for p in future_payments)
    
    closing_balance_selected_date = live_total_dues - future_sales_sum + future_payments_sum
    
    today_orders = Order.query.filter_by(date=date_str, tenant_id=tid).all()
    revenue_finalized = sum(o.total for o in today_orders if o.status == 'finalized')
    
    today_payments = Payment.query.filter_by(date=date_str, tenant_id=tid).all()
    collection_today = sum(p.amount for p in today_payments)
    
    opening_balance = closing_balance_selected_date - revenue_finalized + collection_today

    prev_date_str = (datetime.strptime(date_str, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
    prev_orders = Order.query.filter_by(date=prev_date_str, tenant_id=tid).all()
    prev_revenue = sum(o.total for o in prev_orders if o.status == 'finalized')
    
    pct_change = 0
    if prev_revenue > 0: pct_change = ((revenue_finalized - prev_revenue) / prev_revenue) * 100
    elif revenue_finalized > 0: pct_change = 100

    return jsonify({
        "revenue_today": sum(o.total for o in today_orders),
        "revenue_finalized": revenue_finalized,
        "revenue_pct_change": round(pct_change, 1),
        "collection_today": collection_today,
        "total_dues": round(closing_balance_selected_date, 2),
        "opening_balance": round(opening_balance, 2),
        "active_customers": active_customers
    })

@app.route('/api/employees', methods=['POST'])
@require_auth
def add_employee():
    tid = g.tenant_id
    data = request.json
    count = Employee.query.filter_by(tenant_id=tid).count()
    emp = Employee(id=f"{tid}E{count+1}", tenant_id=tid, name=data['name'], phone=data['phone'], role=data['role'])
    db.session.add(emp)
    db.session.commit()
    return jsonify(emp.to_dict())

@app.route('/api/employees/<id>', methods=['DELETE'])
@require_auth
def delete_employee(id):
    Employee.query.filter_by(id=id, tenant_id=g.tenant_id).delete()
    db.session.commit()
    return jsonify({"message": "Deleted"})

@app.route('/api/products', methods=['POST'])
@require_auth
def add_product():
    tid = g.tenant_id
    data = request.json
    prod = Product(
        id=f"{tid}_{int(datetime.now().timestamp())}", 
        tenant_id=tid, 
        name=data['name'], price=data['price'], unit='Unit', is_active=True
    )
    db.session.add(prod)
    db.session.commit()
    return jsonify(prod.to_dict())

@app.route('/api/products/<id>', methods=['DELETE', 'PUT'])
@require_auth
def mod_product(id):
    prod = Product.query.filter_by(id=id, tenant_id=g.tenant_id).first()
    if not prod: return jsonify({"error": "Not found"}), 404
    
    if request.method == 'DELETE': 
        prod.is_active = False
    elif request.method == 'PUT': 
        prod.price = request.json['price']
    
    db.session.commit()
    return jsonify({"message": "Success"})


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # This block is only for local testing via 'python app.py'
    app.run(debug=False, port=5000)



