from datetime import datetime, timedelta
from .models import db, Job, Receipt
from sqlalchemy import func

def get_dashboard_stats():
    """Get statistics for dashboard summary cards"""
    # Get active jobs
    active_jobs = Job.query.filter_by(status='active').all()
    
    # Calculate stats
    total_jobs = len(active_jobs)
    jobs_over_budget = sum(1 for job in active_jobs if job.profit_margin < 0)
    
    # Average profit margin
    margins = [job.profit_margin for job in active_jobs if job.quoted_price and job.quoted_price > 0]
    avg_profit_margin = sum(margins) / len(margins) if margins else 0
    
    # Money lost this month (negative profits)
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_jobs = [job for job in active_jobs if job.created_at >= current_month]
    money_lost = sum(job.profit_amount for job in month_jobs if job.profit_amount < 0)
    
    return {
        'total_jobs': total_jobs,
        'jobs_over_budget': jobs_over_budget,
        'avg_profit_margin': round(avg_profit_margin, 1),
        'money_lost_month': abs(money_lost)
    }

def get_jobs_summary():
    """Get jobs with calculated profit data"""
    jobs = Job.query.filter_by(status='active').order_by(Job.created_at.desc()).all()
    
    jobs_data = []
    for job in jobs:
        jobs_data.append({
            'id': job.id,
            'job_number': job.job_number,
            'customer_name': job.customer_name,
            'quoted_price': job.quoted_price or 0,
            'current_costs': job.current_costs,
            'profit_amount': job.profit_amount,
            'profit_margin': round(job.profit_margin, 1),
            'status_color': job.status_color,
            'receipt_count': len(job.receipts)
        })
    
    return jobs_data

def get_job_timeline(job_id):
    """Get receipt timeline for a specific job"""
    receipts = Receipt.query.filter_by(job_id=job_id).order_by(Receipt.created_at).all()
    
    timeline = []
    running_total = 0
    
    for receipt in receipts:
        running_total += receipt.total_amount or 0
        timeline.append({
            'date': receipt.created_at.strftime('%Y-%m-%d'),
            'vendor': receipt.vendor or 'Unknown',
            'amount': receipt.total_amount or 0,
            'running_total': running_total,
            'id': receipt.id
        })
    
    return timeline

def generate_daily_summary():
    """Generate daily summary text for SMS/email"""
    stats = get_dashboard_stats()
    
    # Get jobs over budget details
    jobs_over = Job.query.filter_by(status='active').all()
    jobs_over_budget = [job for job in jobs_over if job.profit_margin < 0]
    
    # Find common problematic job types
    problem_categories = {}
    for job in jobs_over_budget:
        # Simple categorization based on customer name patterns
        category = 'General'
        customer_lower = (job.customer_name or '').lower()
        
        if any(word in customer_lower for word in ['plumb', 'pipe', 'toilet', 'sink']):
            category = 'Plumbing'
        elif any(word in customer_lower for word in ['electric', 'wire', 'outlet']):
            category = 'Electrical'
        elif any(word in customer_lower for word in ['roof', 'gutter']):
            category = 'Roofing'
        
        if category not in problem_categories:
            problem_categories[category] = {'count': 0, 'total_loss': 0}
        
        problem_categories[category]['count'] += 1
        problem_categories[category]['total_loss'] += abs(job.profit_amount)
    
    # Build summary text
    summary = f"Daily Summary - {datetime.now().strftime('%B %d, %Y')}\n\n"
    
    if stats['jobs_over_budget'] > 0:
        summary += f"⚠️ {stats['jobs_over_budget']} jobs over budget costing you ${stats['money_lost_month']:,.2f}\n\n"
        
        for category, data in sorted(problem_categories.items(), key=lambda x: x[1]['total_loss'], reverse=True):
            avg_loss = data['total_loss'] / data['count']
            summary += f"• {category} jobs averaging -${avg_loss:,.2f} loss\n"
    else:
        summary += "✅ All jobs are profitable!\n"
    
    summary += f"\nOverall profit margin: {stats['avg_profit_margin']}%\n"
    summary += f"Total active jobs: {stats['total_jobs']}"
    
    return summary

def get_recent_activity(limit=10):
    """Get recent receipt uploads"""
    receipts = Receipt.query.order_by(Receipt.created_at.desc()).limit(limit).all()
    
    activity = []
    for receipt in receipts:
        activity.append({
            'date': receipt.created_at.strftime('%Y-%m-%d %H:%M'),
            'vendor': receipt.vendor or 'Unknown',
            'amount': receipt.total_amount or 0,
            'job_number': receipt.job.job_number if receipt.job else 'Unassigned',
            'upload_method': receipt.upload_method,
            'uploaded_by': receipt.phone_number if receipt.upload_method == 'sms' else receipt.uploaded_by
        })
    
    return activity