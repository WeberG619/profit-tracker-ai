"""
Scheduled tasks for automated alerts and reports
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import logging
from .insights import AlertMonitor, JobInsights, get_profit_trends
from .export_utils import format_daily_summary_text
from .sms_handler import send_sms_response
from .analytics import get_dashboard_stats
import os

logger = logging.getLogger(__name__)

class JobScheduler:
    def __init__(self, app=None):
        self.scheduler = BackgroundScheduler()
        self.app = app
        
    def init_app(self, app):
        """Initialize scheduler with Flask app"""
        self.app = app
        self.start()
    
    def start(self):
        """Start the scheduler with configured jobs"""
        # Daily summary at 6 PM
        self.scheduler.add_job(
            func=self.send_daily_summary,
            trigger="cron",
            hour=18,
            minute=0,
            id='daily_summary',
            replace_existing=True
        )
        
        # Weekly report on Mondays at 9 AM
        self.scheduler.add_job(
            func=self.send_weekly_report,
            trigger="cron",
            day_of_week='mon',
            hour=9,
            minute=0,
            id='weekly_report',
            replace_existing=True
        )
        
        # Check cost alerts every 2 hours during business hours
        self.scheduler.add_job(
            func=self.check_cost_alerts,
            trigger="cron",
            hour='8-18/2',  # Every 2 hours from 8 AM to 6 PM
            minute=0,
            id='cost_alerts',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Scheduler started successfully")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        self.scheduler.shutdown()
    
    def send_daily_summary(self):
        """Send daily summary via SMS/Email"""
        with self.app.app_context():
            try:
                # Get statistics
                stats = get_dashboard_stats()
                insights = JobInsights.find_losing_job_patterns()
                
                # Format summary
                summary_text = format_daily_summary_text(stats, insights)
                
                # Get notification recipients from environment
                recipients = os.getenv('ALERT_PHONE_NUMBERS', '').split(',')
                
                for phone in recipients:
                    if phone.strip():
                        send_sms_response(phone.strip(), summary_text)
                
                logger.info("Daily summary sent successfully")
                
            except Exception as e:
                logger.error(f"Error sending daily summary: {str(e)}")
    
    def send_weekly_report(self):
        """Send weekly profit report"""
        with self.app.app_context():
            try:
                report = AlertMonitor.generate_weekly_report()
                
                # Format report
                report_text = f"""Weekly Profit Report
{report['period']}
{'=' * 40}

Total Jobs: {report['total_jobs']}
Total Revenue: ${report['total_quoted']:,.2f}
Total Costs: ${report['total_costs']:,.2f}
Total Profit: ${report['total_profit']:,.2f}
Average Margin: {report['avg_margin']}%

Profitable Jobs: {report['profitable_jobs']}
Losing Jobs: {report['losing_jobs']}

Best Performer: Job #{report['best_job']}
Worst Performer: Job #{report['worst_job']}
"""
                
                # Send to recipients
                recipients = os.getenv('ALERT_PHONE_NUMBERS', '').split(',')
                
                for phone in recipients:
                    if phone.strip():
                        send_sms_response(phone.strip(), report_text)
                
                logger.info("Weekly report sent successfully")
                
            except Exception as e:
                logger.error(f"Error sending weekly report: {str(e)}")
    
    def check_cost_alerts(self):
        """Check for jobs approaching budget and send alerts"""
        with self.app.app_context():
            try:
                alerts = AlertMonitor.check_cost_alerts(threshold=80)
                
                if alerts:
                    # Send individual alerts for critical jobs (>90%)
                    critical_alerts = [a for a in alerts if a['percentage'] >= 90]
                    
                    for alert in critical_alerts:
                        alert_text = f"""BUDGET ALERT!
Job #{alert['job_number']} ({alert['customer']})
{alert['percentage']}% of budget used

Quoted: ${alert['quoted_price']:,.2f}
Spent: ${alert['current_costs']:,.2f}
Remaining: ${alert['remaining_budget']:,.2f}

Take action to avoid overrun!"""
                        
                        recipients = os.getenv('ALERT_PHONE_NUMBERS', '').split(',')
                        for phone in recipients:
                            if phone.strip():
                                send_sms_response(phone.strip(), alert_text)
                    
                    logger.info(f"Sent {len(critical_alerts)} cost alerts")
                    
            except Exception as e:
                logger.error(f"Error checking cost alerts: {str(e)}")

# Global scheduler instance
job_scheduler = JobScheduler()