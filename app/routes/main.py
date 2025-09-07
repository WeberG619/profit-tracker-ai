"""
Main routes blueprint
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from ..models import db, Receipt, Job
from ..receipt_processor import process_receipt_image
from ..analytics import get_dashboard_stats, get_jobs_summary
from ..insights import JobInsights, get_profit_trends, get_job_type_profitability
from ..auth import company_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
@company_required
def index():
    preselected_job = request.args.get('job')
    return render_template('index.html', preselected_job=preselected_job)

@main_bp.route('/dashboard')
@login_required
@company_required
def dashboard():
    stats = get_dashboard_stats()
    jobs = get_jobs_summary()
    return render_template('dashboard.html', stats=stats, jobs=jobs)

@main_bp.route('/receipts')
@login_required
@company_required
def receipts():
    receipts = Receipt.query.filter_by(company_id=current_user.company_id).order_by(Receipt.created_at.desc()).all()
    return render_template('list.html', receipts=receipts)

@main_bp.route('/insights')
@login_required
@company_required
def insights():
    insights_data = JobInsights.find_losing_job_patterns()
    profit_trends = get_profit_trends(current_user.company_id)
    job_profitability = get_job_type_profitability(current_user.company_id)
    
    return render_template('insights.html', 
                         insights=insights_data,
                         profit_trends=profit_trends,
                         job_profitability=job_profitability)