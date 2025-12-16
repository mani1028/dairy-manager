import os
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, and_
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv('data.env') 

app = Flask(__name__)
CORS(app) 

# --- SUPABASE FIX ---
# SQLAlchemy requires 'postgresql://', but Supabase provides 'postgres://'
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///dairy_manager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class Employee(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(50))

    def to_dict(self):
        return {"id": self.id, "name": self.name, "phone": self.phone, "role": self.role}

class Product(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))

    def to_dict(self):
        return {"id": self.id, "name": self.name, "price": self.price, "unit": self.unit}

class Customer(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True)
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
    customer_id = db.Column(db.String(50), db.ForeignKey('customer.id'), nullable=False)
    product_id = db.Column(db.String(50), nullable=False)
    rate = db.Column(db.Float, nullable=False)

class Order(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    customer_id = db.Column(db.String(50), db.ForeignKey('customer.id'))
    customer_name = db.Column(db.String(100)) 
    date = db.Column(db.String(20), nullable=False) 
    status = db.Column(db.String(20)) 
    total = db.Column(db.Float, default=0.0)
    items = db.relationship('OrderItem', backref='order', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, "customerId": self.customer_id, "customerName": self.customer_name,
            "date": self.date, "status": self.status, "total": self.total,
            "items": [i.to_dict() for i in self.items]
        }

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(50), db.ForeignKey('order.id'))
    product_id = db.Column(db.String(50)) 
    name = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float) 

    def to_dict(self):
        return {"id": self.product_id, "name": self.name, "quantity": self.quantity, "price": self.price}

class Payment(db.Model):
    id = db.Column(db.String(50), primary_key=True)
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

# --- INITIALIZATION ---
def init_db():
    with app.app_context():
        # This creates tables if they don't exist
        db.create_all()
        print("Database initialized. Tables ready.")
        
        # Seed Data (Simplified check)
        if not Product.query.first():
            print("Seeding Initial Products...")
            products_to_seed = [
                ('p1', 'FCM 1L', 70, 'Pkt'), ('p2', 'FCM 500ml', 35, 'Pkt'), ('p3', 'STD 1L', 65, 'Pkt'),
                ('p4', 'STD 500ml', 33, 'Pkt'), ('p5', 'TM 1L', 60, 'Pkt'), ('p6', 'TM 500ml', 30, 'Pkt'),
                ('p7', 'T-SPL 500ml', 32, 'Pkt'), ('p8', 'GOLD Small', 10, 'Pkt'), ('p9', 'TM 130', 15, 'Pkt'),
                ('p10', 'Curd 500gm', 25, 'Pkt'), ('p11', 'Curd Loose', 50, 'Kg'), ('p12', 'DTM 90', 20, 'Pkt'),
                ('p13', 'Skim 10kg', 300, 'Bag'), ('p14', 'TM 10kg', 400, 'Bag'), ('p15', 'Bkt 5kg', 150, 'Bkt'),
                ('p16', 'Bkt 1kg', 40, 'Bkt'), ('p17', 'Paneer 1kg', 350, 'Kg'), ('p18', 'Paneer 500g', 180, 'Pkt'),
                ('p19', 'Paneer 200g', 80, 'Pkt'), ('p20', 'Can 20kg', 1200, 'Can'), ('p21', 'Cowa 500g', 150, 'Pkt'),
                ('p22', 'Cowa 1kg', 300, 'Kg'), ('p23', 'Milk Badam', 20, 'Bottle'), ('p24', 'Butter', 500, 'Kg'),
                ('p25', 'Ghee', 600, 'Kg'),
            ]
            for pid, pname, pprice, punit in products_to_seed:
                db.session.add(Product(id=pid, name=pname, price=pprice, unit=punit))
            db.session.commit()

# --- ROUTES ---

@app.route('/')
def home():
    return send_file('index.html')

@app.route('/reports')
def reports_page():
    return send_file('reports.html')

# 1. AUTH & SYNC
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if data.get('username') == 'admin' and data.get('password') == 'password':
        return jsonify({"token": "valid-token", "role": "admin"})
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/sync', methods=['GET'])
def sync_data():
    customers = [c.to_dict() for c in Customer.query.all()]
    products = [p.to_dict() for p in Product.query.all()]
    employees = [e.to_dict() for e in Employee.query.all()]
    recent_payments = [p.to_dict() for p in Payment.query.order_by(Payment.date.desc()).limit(1000).all()]
    expenses = [e.to_dict() for e in Expense.query.order_by(Expense.date.desc()).limit(1000).all()]
    
    # Get recent orders
    year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    recent_orders = [o.to_dict() for o in Order.query.filter(Order.date >= year_ago).all()]
    
    return jsonify({
        "customers": customers, "products": products, "employees": employees,
        "payments": recent_payments, "expenses": expenses, "orders": recent_orders
    })

# 2. CUSTOMERS
@app.route('/api/customers', methods=['POST'])
def add_customer():
    data = request.json
    if Customer.query.filter_by(phone=data['phone']).first():
        return jsonify({"error": "Phone number already exists"}), 400
    new_id = f"WL{1000 + Customer.query.count() + 1}"
    initial_dues = float(data.get('dues', 0))
    c = Customer(id=new_id, name=data['name'], phone=data['phone'], address=data.get('address'), dues=initial_dues)
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict())

@app.route('/api/customers/<id>', methods=['PUT'])
def update_customer(id):
    data = request.json
    c = Customer.query.get(id)
    if not c: return jsonify({"error": "Not found"}), 404
    c.name = data['name']
    c.phone = data['phone']
    c.address = data.get('address')
    # If explicit update of dues is needed by admin (caution advised)
    if 'dues' in data:
        c.dues = float(data['dues'])
    db.session.commit()
    return jsonify(c.to_dict())

@app.route('/api/customers/<id>', methods=['DELETE'])
def delete_customer(id):
    c = Customer.query.get(id)
    if c:
        db.session.delete(c)
        db.session.commit()
    return jsonify({"message": "Deleted"})

@app.route('/api/customers/<cid>/rates', methods=['POST'])
def update_rates(cid):
    data = request.json
    cust = Customer.query.get(cid)
    if not cust: return jsonify({"error": "Customer not found"}), 404
    rates_map = data.get('rates', {})
    scope = data.get('scope', 'future')

    CustomerRate.query.filter_by(customer_id=cid).delete()
    for pid, rate in rates_map.items():
        db.session.add(CustomerRate(customer_id=cid, product_id=pid, rate=rate))
    
    updated_draft = False
    if scope == 'today':
        today = datetime.now().strftime('%Y-%m-%d')
        draft_order = Order.query.filter_by(customer_id=cid, date=today, status='draft').first()
        if draft_order:
            new_total = 0
            for item in draft_order.items:
                prod = Product.query.get(item.product_id) # Look up by ID now
                if not prod: 
                    # Fallback to name match if ID missing in old data
                    prod = Product.query.filter_by(name=item.name).first()
                
                if prod:
                    new_rate = rates_map.get(prod.id, prod.price)
                    item.price = new_rate
                    new_total += item.quantity * new_rate
            draft_order.total = new_total
            updated_draft = True
    db.session.commit()
    return jsonify({"message": "Rates updated", "draft_updated": updated_draft})

# 3. ORDERS - FIXED: Updates Logic
@app.route('/api/orders', methods=['GET'])
def get_orders():
    date_str = request.args.get('date')
    orders = Order.query.filter_by(date=date_str).all()
    return jsonify([o.to_dict() for o in orders])

@app.route('/api/orders/save', methods=['POST'])
def save_orders():
    data = request.json
    date_str = data['date']
    incoming_orders = data['orders']
    count = 0
    
    for ord_data in incoming_orders:
        customer_id = ord_data['customerId']
        cust = Customer.query.get(customer_id)
        if not cust: continue

        existing = Order.query.filter_by(customer_id=customer_id, date=date_str).first()
        
        # 1. Handle Dues Reversal if updating an already finalized order
        if existing and existing.status == 'finalized':
            # Reverse the old amount from customer dues before applying new amount
            cust.dues -= existing.total
        
        # 2. Update or Create
        if existing:
            existing.total = ord_data['total']
            existing.status = ord_data['status']
            existing.customer_name = ord_data['customerName'] # Update name in case changed
            
            # Clear items and recreate with Product IDs
            OrderItem.query.filter_by(order_id=existing.id).delete()
            for i in ord_data['items']:
                db.session.add(OrderItem(
                    order_id=existing.id, 
                    product_id=i.get('productId'), # Ensure we use ID
                    name=i['name'], 
                    quantity=i['quantity'], 
                    price=i['price']
                ))
        else:
            new_order = Order(
                id=ord_data['id'], 
                customer_id=customer_id, 
                customer_name=ord_data['customerName'],
                date=date_str, 
                status=ord_data['status'], 
                total=ord_data['total']
            )
            db.session.add(new_order)
            for i in ord_data['items']:
                db.session.add(OrderItem(
                    order_id=new_order.id, 
                    product_id=i.get('productId'), # Ensure we use ID
                    name=i['name'], 
                    quantity=i['quantity'], 
                    price=i['price']
                ))
                
        # 3. Apply New Dues if Finalized
        if ord_data['status'] == 'finalized':
            cust.dues += ord_data['total']
            
        count += 1
        
    db.session.commit()
    return jsonify({"message": f"Processed {count} orders. Ledgers updated."})

# 4. PAYMENTS & EXPENSES
@app.route('/api/payments', methods=['POST'])
def add_payment():
    data = request.json
    new_pay = Payment(
        id=str(int(datetime.now().timestamp() * 1000)), customer_id=data['customerId'],
        amount=data['amount'], date=data['date'], collected_by=data.get('collectedBy'), note=data.get('note')
    )
    cust = Customer.query.get(data['customerId'])
    if cust:
        cust.dues -= float(data['amount'])
    db.session.add(new_pay)
    db.session.commit()
    return jsonify({"message": "Payment recorded", "new_dues": cust.dues if cust else 0})

@app.route('/api/expenses', methods=['GET', 'POST'])
def manage_expenses():
    if request.method == 'POST':
        data = request.json
        exp = Expense(
            id=str(int(datetime.now().timestamp())), title=data['title'], amount=data['amount'],
            category=data['category'], date=data['date'], employee_id=data.get('employeeId')
        )
        db.session.add(exp)
        db.session.commit()
        return jsonify(exp.to_dict())
    else:
        start = request.args.get('startDate')
        end = request.args.get('endDate')
        emp_id = request.args.get('employeeId')
        query = Expense.query
        if start and end: query = query.filter(and_(Expense.date >= start, Expense.date <= end))
        if emp_id: query = query.filter_by(employee_id=emp_id)
        exps = query.order_by(Expense.date.desc()).all()
        return jsonify([e.to_dict() for e in exps])

# 5. REPORTS DATA
@app.route('/api/reports/data', methods=['GET'])
def get_report_data():
    start = request.args.get('start')
    end = request.args.get('end')
    
    if not start or not end:
        return jsonify({"error": "Start and End dates required"}), 400

    orders = Order.query.filter(and_(Order.date >= start, Order.date <= end)).all()
    payments = Payment.query.filter(and_(Payment.date >= start, Payment.date <= end)).all()
    expenses = Expense.query.filter(and_(Expense.date >= start, Expense.date <= end)).all()

    return jsonify({
        "orders": [o.to_dict() for o in orders],
        "payments": [p.to_dict() for p in payments],
        "expenses": [e.to_dict() for e in expenses]
    })

# 6. DASHBOARD - FIXED: Historic Calculation
@app.route('/api/dashboard', methods=['GET'])
def dashboard_stats():
    # Target Date
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # 1. Get Live Total Dues (The absolute truth right now)
    live_total_dues = db.session.query(func.sum(Customer.dues)).scalar() or 0
    active_customers = Customer.query.filter_by(status='Active').count()

    # 2. Walk-back Algorithm
    # To find the state of the system on `date_str`, we must reverse 
    # all transactions that happened AFTER `date_str`.
    
    future_orders = Order.query.filter(and_(Order.date > date_str, Order.status == 'finalized')).all()
    future_payments = Payment.query.filter(Payment.date > date_str).all()
    
    # Closing Balance of Selected Date = Live Dues - Future Sales + Future Payments
    future_sales_sum = sum(o.total for o in future_orders)
    future_payments_sum = sum(p.amount for p in future_payments)
    
    closing_balance_selected_date = live_total_dues - future_sales_sum + future_payments_sum
    
    # 3. Calculate Day Specifics
    today_orders = Order.query.filter_by(date=date_str).all()
    revenue_finalized = sum(o.total for o in today_orders if o.status == 'finalized')
    
    today_payments = Payment.query.filter_by(date=date_str).all()
    collection_today = sum(p.amount for p in today_payments)
    
    # 4. Opening Balance = Closing Balance - Today's Sales + Today's Collection
    opening_balance = closing_balance_selected_date - revenue_finalized + collection_today

    # 5. Percentage Change Logic
    prev_date_str = (datetime.strptime(date_str, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
    prev_orders = Order.query.filter_by(date=prev_date_str).all()
    prev_revenue = sum(o.total for o in prev_orders if o.status == 'finalized')
    
    pct_change = 0
    if prev_revenue > 0:
        pct_change = ((revenue_finalized - prev_revenue) / prev_revenue) * 100
    elif revenue_finalized > 0:
        pct_change = 100

    return jsonify({
        "revenue_today": sum(o.total for o in today_orders), # Includes draft
        "revenue_finalized": revenue_finalized,
        "revenue_pct_change": round(pct_change, 1),
        "collection_today": collection_today,
        "total_dues": round(closing_balance_selected_date, 2), # This is the dues at END of selected day
        "opening_balance": round(opening_balance, 2), # This is the dues at START of selected day
        "active_customers": active_customers
    })

@app.route('/api/employees', methods=['POST'])
def add_employee():
    data = request.json
    emp = Employee(id=f"E{100+Employee.query.count()+1}", name=data['name'], phone=data['phone'], role=data['role'])
    db.session.add(emp)
    db.session.commit()
    return jsonify(emp.to_dict())

@app.route('/api/employees/<id>', methods=['DELETE'])
def delete_employee(id):
    Employee.query.filter_by(id=id).delete()
    db.session.commit()
    return jsonify({"message": "Deleted"})

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    prod = Product(id=f"p{int(datetime.now().timestamp())}", name=data['name'], price=data['price'], unit='Unit')
    db.session.add(prod)
    db.session.commit()
    return jsonify(prod.to_dict())

@app.route('/api/products/<id>', methods=['DELETE', 'PUT'])
def mod_product(id):
    prod = Product.query.get(id)
    if not prod: return jsonify({"error": "Not found"}), 404
    if request.method == 'DELETE': db.session.delete(prod)
    elif request.method == 'PUT': prod.price = request.json['price']
    db.session.commit()
    return jsonify({"message": "Success"})

# Initialize Database on Start
init_db()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
