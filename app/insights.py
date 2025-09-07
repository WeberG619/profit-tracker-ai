"""
Intelligent insights and pattern detection for job profitability
"""

from datetime import datetime, timedelta
from collections import defaultdict
import re
from sqlalchemy import func, and_
from .models import db, Job, Receipt
import statistics

class JobInsights:
    """Pattern detection and job analysis"""
    
    @staticmethod
    def find_losing_job_patterns():
        """Find job types that consistently lose money"""
        jobs = Job.query.filter_by(status='active').all()
        
        # Group jobs by keywords
        pattern_groups = defaultdict(list)
        keywords = [
            'toilet', 'sink', 'pipe', 'plumb', 'water heater', 'faucet',  # Plumbing
            'outlet', 'panel', 'breaker', 'wire', 'switch', 'electric',   # Electrical
            'hvac', 'ac', 'furnace', 'duct', 'thermostat',               # HVAC
            'roof', 'shingle', 'gutter', 'flashing',                      # Roofing
            'paint', 'drywall', 'floor', 'tile', 'cabinet'                # General
        ]
        
        for job in jobs:
            job_text = (job.customer_name or '').lower()
            
            # Find matching keywords
            matched = False
            for keyword in keywords:
                if keyword in job_text:
                    pattern_groups[keyword].append({
                        'job': job,
                        'profit_margin': job.profit_margin,
                        'profit_amount': job.profit_amount
                    })
                    matched = True
            
            if not matched:
                pattern_groups['other'].append({
                    'job': job,
                    'profit_margin': job.profit_margin,
                    'profit_amount': job.profit_amount
                })
        
        # Analyze each pattern group
        insights = []
        for keyword, job_list in pattern_groups.items():
            if len(job_list) >= 2:  # Need at least 2 jobs for pattern
                margins = [j['profit_margin'] for j in job_list]
                avg_margin = sum(margins) / len(margins)
                
                # Count losing jobs
                losing_jobs = [j for j in job_list if j['profit_margin'] < 5]
                losing_percentage = (len(losing_jobs) / len(job_list)) * 100
                
                if losing_percentage >= 50 or avg_margin < 10:
                    insights.append({
                        'keyword': keyword,
                        'job_count': len(job_list),
                        'avg_margin': round(avg_margin, 1),
                        'losing_percentage': round(losing_percentage, 1),
                        'total_lost': sum(j['profit_amount'] for j in losing_jobs if j['profit_amount'] < 0)
                    })
        
        # Sort by severity (lowest margin first)
        insights.sort(key=lambda x: x['avg_margin'])
        return insights
    
    @staticmethod
    def calculate_job_duration_analysis():
        """Analyze which jobs take longest based on receipt timeline"""
        jobs = Job.query.filter_by(status='active').all()
        
        duration_analysis = []
        for job in jobs:
            if job.receipts:
                # Get first and last receipt dates
                receipt_dates = [r.created_at for r in job.receipts]
                duration = (max(receipt_dates) - min(receipt_dates)).days
                
                duration_analysis.append({
                    'job': job,
                    'duration_days': duration,
                    'receipt_count': len(job.receipts),
                    'avg_receipts_per_day': len(job.receipts) / (duration + 1)
                })
        
        # Sort by duration
        duration_analysis.sort(key=lambda x: x['duration_days'], reverse=True)
        return duration_analysis[:10]  # Top 10 longest jobs

class PriceRecommendation:
    """Price recommendation engine based on historical data"""
    
    @staticmethod
    def get_pricing_suggestions(job_description, target_margin=25):
        """Get pricing suggestions based on similar jobs"""
        # Extract keywords from description
        keywords = job_description.lower().split()
        
        # Find similar completed jobs
        all_jobs = Job.query.filter_by(status='active').all()
        similar_jobs = []
        
        for job in all_jobs:
            if job.current_costs > 0:  # Only jobs with actual costs
                job_text = (job.customer_name or '').lower()
                # Count matching keywords
                matches = sum(1 for keyword in keywords if keyword in job_text)
                if matches > 0:
                    similar_jobs.append({
                        'job': job,
                        'matches': matches,
                        'actual_cost': job.current_costs,
                        'quoted': job.quoted_price,
                        'margin': job.profit_margin
                    })
        
        if not similar_jobs:
            return None
        
        # Sort by relevance (most matches first)
        similar_jobs.sort(key=lambda x: x['matches'], reverse=True)
        
        # Take top 5 most similar
        relevant_jobs = similar_jobs[:5]
        
        # Calculate statistics
        costs = [j['actual_cost'] for j in relevant_jobs]
        quotes = [j['quoted'] for j in relevant_jobs]
        margins = [j['margin'] for j in relevant_jobs]
        
        avg_cost = sum(costs) / len(costs)
        avg_quote = sum(quotes) / len(quotes)
        avg_margin = sum(margins) / len(margins)
        
        # Calculate recommended price for target margin
        recommended_price = avg_cost * (1 + target_margin / 100)
        
        return {
            'similar_jobs_found': len(relevant_jobs),
            'avg_actual_cost': round(avg_cost, 2),
            'avg_quoted_price': round(avg_quote, 2),
            'avg_profit_margin': round(avg_margin, 1),
            'recommended_price': round(recommended_price, 2),
            'target_margin': target_margin,
            'confidence': 'high' if len(relevant_jobs) >= 5 else 'medium' if len(relevant_jobs) >= 3 else 'low'
        }

class AlertMonitor:
    """Monitor jobs and send alerts"""
    
    @staticmethod
    def check_cost_alerts(threshold=80):
        """Find jobs approaching budget threshold"""
        jobs = Job.query.filter_by(status='active').all()
        alerts = []
        
        for job in jobs:
            if job.quoted_price > 0:
                cost_percentage = (job.current_costs / job.quoted_price) * 100
                
                if cost_percentage >= threshold and cost_percentage < 100:
                    alerts.append({
                        'job_id': job.id,
                        'job_number': job.job_number,
                        'customer': job.customer_name,
                        'quoted_price': job.quoted_price,
                        'current_costs': job.current_costs,
                        'percentage': round(cost_percentage, 1),
                        'remaining_budget': job.quoted_price - job.current_costs
                    })
        
        return alerts
    
    @staticmethod
    def generate_weekly_report():
        """Generate weekly profit report"""
        # Get jobs from last week
        week_ago = datetime.now() - timedelta(days=7)
        recent_jobs = Job.query.filter(Job.created_at >= week_ago).all()
        
        # Calculate metrics
        total_quoted = sum(j.quoted_price or 0 for j in recent_jobs)
        total_costs = sum(j.current_costs for j in recent_jobs)
        total_profit = sum(j.profit_amount for j in recent_jobs)
        
        profitable_jobs = [j for j in recent_jobs if j.profit_margin > 20]
        losing_jobs = [j for j in recent_jobs if j.profit_margin < 0]
        
        return {
            'period': f"{week_ago.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}",
            'total_jobs': len(recent_jobs),
            'total_quoted': round(total_quoted, 2),
            'total_costs': round(total_costs, 2),
            'total_profit': round(total_profit, 2),
            'avg_margin': round((total_profit / total_quoted * 100) if total_quoted > 0 else 0, 1),
            'profitable_jobs': len(profitable_jobs),
            'losing_jobs': len(losing_jobs),
            'best_job': max(recent_jobs, key=lambda j: j.profit_margin).job_number if recent_jobs else None,
            'worst_job': min(recent_jobs, key=lambda j: j.profit_margin).job_number if recent_jobs else None
        }

def get_profit_trends(days=30):
    """Get profit trends over time"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Get all jobs in date range
    jobs = Job.query.filter(Job.created_at >= start_date).all()
    
    # Group by date
    daily_profits = defaultdict(lambda: {'revenue': 0, 'costs': 0, 'profit': 0, 'count': 0})
    
    for job in jobs:
        date_key = job.created_at.date()
        daily_profits[date_key]['revenue'] += job.quoted_price or 0
        daily_profits[date_key]['costs'] += job.current_costs
        daily_profits[date_key]['profit'] += job.profit_amount
        daily_profits[date_key]['count'] += 1
    
    # Convert to list for charting
    trends = []
    current_date = start_date.date()
    while current_date <= end_date.date():
        data = daily_profits.get(current_date, {'revenue': 0, 'costs': 0, 'profit': 0, 'count': 0})
        trends.append({
            'date': current_date.isoformat(),
            'revenue': data['revenue'],
            'costs': data['costs'],
            'profit': data['profit'],
            'jobs': data['count']
        })
        current_date += timedelta(days=1)
    
    return trends

def get_job_type_profitability():
    """Analyze profitability by job type"""
    insights = JobInsights.find_losing_job_patterns()
    
    # Get all pattern groups for complete picture
    jobs = Job.query.filter_by(status='active').all()
    all_patterns = defaultdict(list)
    
    keywords = [
        ('Plumbing', ['toilet', 'sink', 'pipe', 'plumb', 'water heater', 'faucet']),
        ('Electrical', ['outlet', 'panel', 'breaker', 'wire', 'switch', 'electric']),
        ('HVAC', ['hvac', 'ac', 'furnace', 'duct', 'thermostat']),
        ('Roofing', ['roof', 'shingle', 'gutter', 'flashing']),
        ('General', ['paint', 'drywall', 'floor', 'tile', 'cabinet'])
    ]
    
    for job in jobs:
        job_text = (job.customer_name or '').lower()
        matched = False
        
        for category, category_keywords in keywords:
            if any(kw in job_text for kw in category_keywords):
                all_patterns[category].append(job)
                matched = True
                break
        
        if not matched:
            all_patterns['Other'].append(job)
    
    # Calculate stats for each category
    profitability_data = []
    for category, job_list in all_patterns.items():
        if job_list:
            margins = [j.profit_margin for j in job_list]
            profitability_data.append({
                'category': category,
                'job_count': len(job_list),
                'avg_margin': round(sum(margins) / len(margins), 1),
                'total_profit': round(sum(j.profit_amount for j in job_list), 2)
            })
    
    # Sort by average margin
    profitability_data.sort(key=lambda x: x['avg_margin'], reverse=True)
    return profitability_data