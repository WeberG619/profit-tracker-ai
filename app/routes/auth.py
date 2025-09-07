"""
Authentication routes blueprint
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from ..models import db, User, Company
from ..auth import login_manager

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Create company first
        company = Company(
            name=request.form.get('company_name'),
            phone_number=request.form.get('phone_number')
        )
        db.session.add(company)
        db.session.commit()
        
        # Create user
        user = User(
            username=request.form.get('username'),
            email=request.form.get('email'),
            company_id=company.id,
            is_admin=True  # First user is admin
        )
        user.set_password(request.form.get('password'))
        
        try:
            db.session.add(user)
            db.session.commit()
            
            login_user(user)
            flash('Account created successfully!', 'success')
            return redirect(url_for('main.setup'))
            
        except Exception as e:
            db.session.rollback()
            flash('Username or email already exists', 'error')
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/setup')
@login_required
def setup():
    return render_template('setup.html', company=current_user.company)