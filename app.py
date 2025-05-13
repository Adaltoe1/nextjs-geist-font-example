from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///financial_control.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # 'entrada' ou 'despesa'
    payment_method = db.Column(db.String(20))  # 'dinheiro', 'cheque', 'cartao'
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(100))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:  # In production, use proper password hashing
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha inválidos', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Calculate totals
    transactions = Transaction.query.all()
    total_income = sum(t.amount for t in transactions if t.type == 'entrada')
    total_expenses = sum(t.amount for t in transactions if t.type == 'despesa')
    balance = total_income - total_expenses
    
    return render_template('dashboard.html',
                         transactions=transactions,
                         total_income=total_income,
                         total_expenses=total_expenses,
                         balance=balance)

@app.route('/transactions', methods=['GET'])
@login_required
def transactions():
    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    return render_template('transactions.html', transactions=transactions)

@app.route('/transaction/new', methods=['GET', 'POST'])
@login_required
def create_transaction():
    if request.method == 'POST':
        try:
            transaction = Transaction(
                type=request.form['type'],
                payment_method=request.form['payment_method'],
                amount=float(request.form['amount']),
                description=request.form['description']
            )
            db.session.add(transaction)
            db.session.commit()
            flash('Transação registrada com sucesso!', 'success')
            return redirect(url_for('transactions'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar transação: {str(e)}', 'danger')
    
    return render_template('create_transaction.html')

@app.route('/clients', methods=['GET', 'POST'])
@login_required
def clients():
    if request.method == 'POST':
        try:
            client = Client(
                name=request.form['name'],
                email=request.form['email'],
                phone=request.form['phone']
            )
            db.session.add(client)
            db.session.commit()
            flash('Cliente cadastrado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar cliente: {str(e)}', 'danger')
    
    clients = Client.query.all()
    return render_template('clients.html', clients=clients)

@app.route('/companies', methods=['GET', 'POST'])
@login_required
def companies():
    if request.method == 'POST':
        try:
            company = Company(
                name=request.form['name'],
                contact=request.form['contact']
            )
            db.session.add(company)
            db.session.commit()
            flash('Empresa cadastrada com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar empresa: {str(e)}', 'danger')
    
    companies = Company.query.all()
    return render_template('companies.html', companies=companies)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create default admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password='admin123')  # In production, use proper password hashing
            db.session.add(admin)
            db.session.commit()
    app.run(host='0.0.0.0', port=8000, debug=True)
