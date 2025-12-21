import os
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, jsonify, request, send_file, g
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, and_, inspect, text
from sqlalchemy.exc import OperationalError, IntegrityError
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

# --- CONFIGURATION ---
load_dotenv('data.env') 

app = Flask(__name__)
# PRODUCTION NOTE: Change this key in your environment variables for security
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-to-a-secure-random-key-in-production')
CORS(app) 

# --- DATABASE SETUP ---
database_url = os.environ.get('DATABASE_URL')

# Fallback for local testing
if not database_url:
    # REPLACE WITH YOUR ACTUAL DATABASE URL FOR LOCAL TESTING
    database_url = "postgresql://postgres.tkgnfijktdmvgvsdbneq:IKyNw6s0HdwGpKQ1@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# --- DEFAULT PRODUCTS LIST ---
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

# --- MODELS ---

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

class Employee(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('dairy_tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(50))
    # New columns for enhancements
    designation = db.Column(db.String(100))
    username = db.Column(db.String(50)) # Link to DairyUser if exists

    def to_dict(self): 
        return {
            "id": self.id, 
            "name": self.name, 
            "phone": self.phone, 
            "role": self.role,
            "designation": self.designation,
            "username": self.username
        }

class Product(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('dairy_tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self): return {"id": self.id, "name": self.name, "price": self.price, "unit": self.unit, "isActive": self.is_active}

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
        return {"id": self.id, "name": self.name, "phone": self.phone, "address": self.address, "dues": self.dues, "status": self.status, "customRates": custom_rates}

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
            try: items_list = json.loads(self.items_json)
            except: items_list = []
        formatted_items = []
        for i in items_list:
            formatted_items.append({
                "id": i.get('productId') or i.get('id'),
                "name": i.get('name'),
                "quantity": i.get('quantity'),
                "price": i.get('price')
            })
        return {"id": self.id, "customerId": self.customer_id, "customerName": self.customer_name, "date": self.date, "status": self.status, "total": self.total, "items": formatted_items}

class Payment(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('dairy_tenant.id'), nullable=False)
    customer_id = db.Column(db.String(50), db.ForeignKey('customer.id'))
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(20))
    collected_by = db.Column(db.String(100))
    note = db.Column(db.String(200))

    def to_dict(self): return {"id": self.id, "customerId": self.customer_id, "amount": self.amount, "date": self.date, "collectedBy": self.collected_by, "note": self.note}

class Expense(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('dairy_tenant.id'), nullable=False)
    title = db.Column(db.String(200))
    amount = db.Column(db.Float)
    category = db.Column(db.String(50))
    date = db.Column(db.String(20))
    employee_id = db.Column(db.String(50)) 

    def to_dict(self): return {"id": self.id, "title": self.title, "amount": self.amount, "category": self.category, "date": self.date, "employeeId": self.employee_id}

# --- HELPERS ---

def generate_tenant_id(location_name):
    codes = {"Warangal": "WL", "Hyderabad": "HYD", "Karimnagar": "KR"}
    code = codes.get(location_name, location_name[:3].upper() if location_name else "GEN")
    last_tenant = DairyTenant.query.filter_by(location_code=code).order_by(DairyTenant.location_seq.desc()).first()
    seq = (last_tenant.location_seq + 1) if last_tenant else 1
    return f"{code}{seq:02d}", code, seq

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header: return jsonify({'error': 'Missing token'}), 401
        try:
            token = auth_header.split(" ")[1]
            data = serializer.loads(token, max_age=86400)
            g.tenant_id = data['tenant_id']
            g.user_id = data['user_id']
            
            # Load Role
            user = DairyUser.query.get(g.user_id)
            g.role = user.role if user else 'admin'
            
        except Exception: return jsonify({'error': 'Invalid or expired token'}), 401
        return f(*args, **kwargs)
    return decorated

def require_role(roles):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if g.role not in roles:
                return jsonify({"error": "Access denied"}), 403
            return f(*args, **kwargs)
        return decorated
    return wrapper

# --- ROUTES ---

@app.route('/')
@app.route('/index.html')
def home(): return send_file('index.html')

@app.route('/reports.html')
def reports_page(): return send_file('reports.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    business_name = data.get('business_name')
    location = data.get('location')
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password or not business_name: return jsonify({"error": "Missing required fields"}), 400
    if DairyUser.query.filter_by(username=username).first(): return jsonify({"error": "Username taken"}), 400

    tid, code, seq = generate_tenant_id(location)
    tenant = DairyTenant(id=tid, name=business_name, location_code=code, location_seq=seq)
    db.session.add(tenant)

    user = DairyUser(username=username, password=password, tenant_id=tid, role='admin')
    db.session.add(user)
    
    # Auto-seed products on register
    for p in DEFAULT_PRODUCTS:
        new_prod = Product(
            id=f"{tid}_{p['code']}",
            tenant_id=tid,
            name=p['name'],
            price=p['price'],
            unit=p['unit'],
            is_active=True
        )
        db.session.add(new_prod)
        
    db.session.commit()
    token = serializer.dumps({'user_id': user.id, 'tenant_id': user.tenant_id})
    return jsonify({"message": "Account created!", "token": token, "tenant_id": tid, "business_name": tenant.name})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = DairyUser.query.filter_by(username=data.get('username')).first()
    
    if user and user.password == data.get('password'):
        # --- SELF-HEALING: Check if products exist, if not, create them ---
        existing_products_count = Product.query.filter_by(tenant_id=user.tenant_id).count()
        if existing_products_count == 0:
            print(f"Auto-seeding products for {user.tenant_id}")
            for p in DEFAULT_PRODUCTS:
                new_prod = Product(
                    id=f"{user.tenant_id}_{p['code']}",
                    tenant_id=user.tenant_id,
                    name=p['name'],
                    price=p['price'],
                    unit=p['unit'],
                    is_active=True
                )
                db.session.add(new_prod)
            db.session.commit()
        # ------------------------------------------------------------------

        token = serializer.dumps({'user_id': user.id, 'tenant_id': user.tenant_id})
        tenant = DairyTenant.query.get(user.tenant_id)
        return jsonify({
            "token": token,
            "tenant_id": user.tenant_id,
            "business_name": tenant.name,
            "role": user.role 
        })
        
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/staff', methods=['POST'])
@require_auth
@require_role(['admin'])
def add_staff():
    data = request.json
    tid = g.tenant_id
    
    username = data.get('username')
    password = data.get('password')
    
    # Optional Login Creation
    if username and password:
        if DairyUser.query.filter_by(username=username).first():
            return jsonify({"error": "Username already taken"}), 400
        
        user = DairyUser(
            username=username,
            password=password,
            role=data['role'],
            tenant_id=tid
        )
        db.session.add(user)
        linked_username = username
    else:
        linked_username = None

    # Create Employee Record
    emp = Employee(
        id=f"{tid}E{int(datetime.now().timestamp())}",
        tenant_id=tid,
        name=data['name'],
        phone=data['phone'],
        role=data['role'],
        designation=data.get('designation', ''),
        username=linked_username
    )
    db.session.add(emp)

    db.session.commit()
    return jsonify({"message": "Staff added successfully"})

@app.route('/api/employees/<id>', methods=['PUT'])
@require_auth
@require_role(['admin'])
def update_staff(id):
    data = request.json
    tid = g.tenant_id
    
    emp = Employee.query.filter_by(id=id, tenant_id=tid).first()
    if not emp:
        return jsonify({"error": "Employee not found"}), 404

    # Update basic fields
    emp.name = data['name']
    emp.phone = data['phone']
    emp.role = data['role']
    emp.designation = data.get('designation', '')

    # Handle Login Updates
    username = data.get('username')
    password = data.get('password')

    # Case 1: User wants to set/change username
    if username:
        # Check if this employee already has a linked user
        if emp.username and emp.username != username:
            # Username changed? Check availability of new one
            if DairyUser.query.filter_by(username=username).first():
                return jsonify({"error": "New username is already taken"}), 400
            
            # Find old user and update or delete? 
            # Strategy: Find user by old username and update it
            old_user = DairyUser.query.filter_by(username=emp.username).first()
            if old_user:
                old_user.username = username
                old_user.role = emp.role
                if password: # Update password only if provided
                    old_user.password = password
            else:
                 # Should not happen but fallback: create new
                 new_user = DairyUser(username=username, password=password or "temp123", role=emp.role, tenant_id=tid)
                 db.session.add(new_user)
            
            emp.username = username

        elif not emp.username:
            # Creating NEW login for existing employee
            if DairyUser.query.filter_by(username=username).first():
                return jsonify({"error": "Username is already taken"}), 400
            if not password:
                return jsonify({"error": "Password required when creating new login"}), 400
            
            new_user = DairyUser(username=username, password=password, role=emp.role, tenant_id=tid)
            db.session.add(new_user)
            emp.username = username
        
        else:
            # Username matches existing. Update password/role if needed
            existing_user = DairyUser.query.filter_by(username=username).first()
            if existing_user:
                existing_user.role = emp.role
                if password: # Update password only if provided
                    existing_user.password = password
    
    db.session.commit()
    return jsonify({"message": "Staff updated successfully"})

@app.route('/api/employees/<id>', methods=['DELETE'])
@require_auth
@require_role(['admin'])
def delete_employee(id):
    emp = Employee.query.filter_by(id=id, tenant_id=g.tenant_id).first()
    if emp:
        # If employee has a login, delete that too
        if emp.username:
            DairyUser.query.filter_by(username=emp.username).delete()
        
        db.session.delete(emp)
        db.session.commit()
    return jsonify({"message": "Deleted"})

@app.route('/api/agent/dues', methods=['GET'])
@require_auth
@require_role(['admin', 'collection_agent'])
def agent_dues():
    tid = g.tenant_id
    customers = Customer.query.filter_by(tenant_id=tid).all()
    output = []

    for c in customers:
        # Calculate totals dynamically to be safe
        orders = db.session.query(func.sum(Order.total)).filter_by(
            tenant_id=tid, customer_id=c.id, status='finalized'
        ).scalar() or 0

        payments = db.session.query(func.sum(Payment.amount)).filter_by(
            tenant_id=tid, customer_id=c.id
        ).scalar() or 0

        due_amount = orders - payments
        
        if due_amount != 0 or orders > 0:
            output.append({
                "customerId": c.id,
                "name": c.name,
                "totalOrders": orders,
                "totalPayments": payments,
                "due": due_amount
            })

    return jsonify(output)

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
        return jsonify({"customers": customers, "products": products, "employees": employees, "payments": recent_payments, "expenses": expenses, "orders": recent_orders})
    except OperationalError: return jsonify({"error": "Database error."}), 500

@app.route('/api/customers', methods=['POST'])
@require_auth
def add_customer():
    data = request.json
    tid = g.tenant_id
    if Customer.query.filter_by(tenant_id=tid, phone=data['phone']).first(): return jsonify({"error": "Phone exists"}), 400
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
    if request.method == 'DELETE': db.session.delete(c)
    else:
        data = request.json
        c.name, c.phone, c.address = data['name'], data['phone'], data.get('address')
        if 'dues' in data: c.dues = float(data['dues'])
    db.session.commit()
    return jsonify(c.to_dict() if request.method == 'PUT' else {"message": "Deleted"})

@app.route('/api/customers/<cid>/rates', methods=['POST'])
@require_auth
def update_rates(cid):
    data = request.json
    tid = g.tenant_id
    CustomerRate.query.filter_by(customer_id=cid, tenant_id=tid).delete()
    for pid, rate in data.get('rates', {}).items():
        db.session.add(CustomerRate(tenant_id=tid, customer_id=cid, product_id=pid, rate=rate))
    
    if data.get('scope') == 'today':
        today = datetime.now().strftime('%Y-%m-%d')
        draft_order = Order.query.filter_by(customer_id=cid, date=today, status='draft', tenant_id=tid).first()
        if draft_order:
            items = json.loads(draft_order.items_json) if draft_order.items_json else []
            new_total = 0
            for item in items:
                pid = item.get('productId') or item.get('id')
                prod = Product.query.filter_by(id=pid, tenant_id=tid).first()
                if prod:
                    new_rate = data.get('rates', {}).get(prod.id, prod.price)
                    item['price'] = new_rate
                    new_total += item['quantity'] * new_rate
            draft_order.items_json = json.dumps(items)
            draft_order.total = new_total
    db.session.commit()
    return jsonify({"message": "Rates updated"})

@app.route('/api/sheets/finalize', methods=['POST'])
@require_auth
def finalize_sheet():
    data = request.json
    tid, date_str = g.tenant_id, data.get('date')
    if not date_str: return jsonify({"error": "Date required"}), 400
    orders = Order.query.filter_by(date=date_str, tenant_id=tid).all()
    count = 0
    for o in orders:
        if o.status != 'finalized':
            cust = Customer.query.filter_by(id=o.customer_id, tenant_id=tid).first()
            if cust: cust.dues += o.total
            o.status = 'finalized'
            count += 1
    db.session.commit()
    return jsonify({"success": True, "message": f"Finalized {count} orders"})

@app.route('/api/orders', methods=['GET'])
@require_auth
def get_orders():
    orders = Order.query.filter_by(date=request.args.get('date'), tenant_id=g.tenant_id).all()
    return jsonify([o.to_dict() for o in orders])

@app.route('/api/orders/save', methods=['POST'])
@require_auth
def save_orders():
    data, tid = request.json, g.tenant_id
    date_str, count = data['date'], 0
    for ord_data in data['orders']:
        cust = Customer.query.filter_by(id=ord_data['customerId'], tenant_id=tid).first()
        if not cust: continue
        existing = Order.query.filter_by(customer_id=ord_data['customerId'], date=date_str, tenant_id=tid).first()
        if existing and existing.status == 'finalized': cust.dues -= existing.total
        
        items_json_str = json.dumps(ord_data['items'])
        if existing:
            existing.total = ord_data['total']
            existing.status = ord_data['status']
            existing.customer_name = ord_data['customerName']
            existing.items_json = items_json_str
        else:
            db.session.add(Order(id=ord_data['id'], tenant_id=tid, customer_id=cust.id, customer_name=ord_data['customerName'], date=date_str, status=ord_data['status'], total=ord_data['total'], items_json=items_json_str))
        
        if ord_data['status'] == 'finalized': cust.dues += ord_data['total']
        count += 1
    db.session.commit()
    return jsonify({"message": f"Processed {count} orders."})

@app.route('/api/payments', methods=['POST'])
@require_auth
def add_payment():
    data, tid = request.json, g.tenant_id
    cust = Customer.query.filter_by(id=data['customerId'], tenant_id=tid).first()
    if not cust: return jsonify({"error": "Customer not found"}), 404
    db.session.add(Payment(id=str(int(datetime.now().timestamp() * 1000)), tenant_id=tid, customer_id=data['customerId'], amount=data['amount'], date=data['date'], collected_by=data.get('collectedBy'), note=data.get('note')))
    cust.dues -= float(data['amount'])
    db.session.commit()
    return jsonify({"message": "Payment recorded"})

@app.route('/api/expenses', methods=['GET', 'POST'])
@require_auth
def manage_expenses():
    tid = g.tenant_id
    if request.method == 'POST':
        data = request.json
        exp = Expense(id=str(int(datetime.now().timestamp())), tenant_id=tid, title=data['title'], amount=data['amount'], category=data['category'], date=data['date'], employee_id=data.get('employeeId'))
        db.session.add(exp)
        db.session.commit()
        return jsonify(exp.to_dict())
    else:
        query = Expense.query.filter_by(tenant_id=tid)
        if request.args.get('startDate') and request.args.get('endDate'): query = query.filter(and_(Expense.date >= request.args.get('startDate'), Expense.date <= request.args.get('endDate')))
        if request.args.get('employeeId'): query = query.filter_by(employee_id=request.args.get('employeeId'))
        return jsonify([e.to_dict() for e in query.order_by(Expense.date.desc()).all()])

@app.route('/api/reports/data', methods=['GET'])
@require_auth
def get_report_data():
    tid, start, end = g.tenant_id, request.args.get('start'), request.args.get('end')
    if not start or not end: return jsonify({"error": "Dates required"}), 400
    return jsonify({
        "orders": [o.to_dict() for o in Order.query.filter(and_(Order.tenant_id == tid, Order.date >= start, Order.date <= end)).all()],
        "payments": [p.to_dict() for p in Payment.query.filter(and_(Payment.tenant_id == tid, Payment.date >= start, Payment.date <= end)).all()],
        "expenses": [e.to_dict() for e in Expense.query.filter(and_(Expense.tenant_id == tid, Expense.date >= start, Expense.date <= end)).all()]
    })

@app.route('/api/dashboard', methods=['GET'])
@require_auth
def dashboard_stats():
    tid, date_str = g.tenant_id, request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    live_total_dues = db.session.query(func.sum(Customer.dues)).filter_by(tenant_id=tid).scalar() or 0
    active_customers = Customer.query.filter_by(tenant_id=tid, status='Active').count()
    
    future_sales = sum(o.total for o in Order.query.filter(and_(Order.tenant_id == tid, Order.date > date_str, Order.status == 'finalized')).all())
    future_collections = sum(p.amount for p in Payment.query.filter(and_(Payment.tenant_id == tid, Payment.date > date_str)).all())
    
    today_orders = Order.query.filter_by(date=date_str, tenant_id=tid).all()
    revenue_finalized = sum(o.total for o in today_orders if o.status == 'finalized')
    collection_today = sum(p.amount for p in Payment.query.filter_by(date=date_str, tenant_id=tid).all())
    
    total_dues_on_date = live_total_dues - future_sales + future_collections
    opening_balance = total_dues_on_date - revenue_finalized + collection_today

    prev_date = (datetime.strptime(date_str, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
    prev_rev = sum(o.total for o in Order.query.filter_by(date=prev_date, tenant_id=tid).all() if o.status == 'finalized')
    pct = ((revenue_finalized - prev_rev) / prev_rev * 100) if prev_rev > 0 else (100 if revenue_finalized > 0 else 0)

    return jsonify({"revenue_today": sum(o.total for o in today_orders), "revenue_finalized": revenue_finalized, "revenue_pct_change": round(pct, 1), "collection_today": collection_today, "total_dues": round(total_dues_on_date, 2), "opening_balance": round(opening_balance, 2), "active_customers": active_customers})

@app.route('/api/products', methods=['POST'])
@require_auth
def add_product():
    data, tid = request.json, g.tenant_id
    prod = Product(id=f"{tid}_{int(datetime.now().timestamp())}", tenant_id=tid, name=data['name'], price=data['price'], unit='Unit', is_active=True)
    db.session.add(prod)
    db.session.commit()
    return jsonify(prod.to_dict())

@app.route('/api/products/<id>', methods=['DELETE', 'PUT'])
@require_auth
def mod_product(id):
    prod = Product.query.filter_by(id=id, tenant_id=g.tenant_id).first()
    if not prod: return jsonify({"error": "Not found"}), 404
    if request.method == 'DELETE': prod.is_active = False
    elif request.method == 'PUT': prod.price = request.json['price']
    db.session.commit()
    return jsonify({"message": "Success"})


# --- AUTO-CREATE TABLES & MIGRATION ON STARTUP ---
with app.app_context():
    db.create_all()
    
    # --- AUTO MIGRATION LOGIC FOR NEW COLUMNS ---
    try:
        inspector = inspect(db.engine)
        if 'employee' in inspector.get_table_names():
            cols = [c['name'] for c in inspector.get_columns('employee')]
            with db.engine.connect() as conn:
                if 'designation' not in cols:
                    print("Migrating: Adding designation column")
                    conn.execute(text("ALTER TABLE employee ADD COLUMN designation VARCHAR(100)"))
                if 'username' not in cols:
                    print("Migrating: Adding username column")
                    conn.execute(text("ALTER TABLE employee ADD COLUMN username VARCHAR(50)"))
                conn.commit()
    except Exception as e:
        print(f"Migration warning (can be ignored if fresh DB): {e}")


if __name__ == '__main__':
    app.run(debug=False, port=5000)