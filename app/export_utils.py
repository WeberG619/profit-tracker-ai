"""
Export utilities for receipts, reports, and data
"""

import csv
import io
import zipfile
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import os

def export_receipts_csv(receipts):
    """Export receipts to CSV format for QuickBooks"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # QuickBooks compatible headers
    writer.writerow([
        'Date', 'Transaction Type', 'Num', 'Name', 'Memo', 'Account', 
        'Debit', 'Credit', 'Job', 'Class'
    ])
    
    for receipt in receipts:
        # Each receipt as expense transaction
        writer.writerow([
            receipt.date.strftime('%m/%d/%Y') if receipt.date else receipt.created_at.strftime('%m/%d/%Y'),
            'Expense',
            receipt.receipt_number or '',
            receipt.vendor or 'Unknown Vendor',
            f"Receipt - {receipt.vendor or 'Unknown'}",
            'Job Expenses',
            receipt.total or 0,
            '',  # Credit column empty for expenses
            f"Job {receipt.job.job_number}" if receipt.job else '',
            ''  # Class field
        ])
        
        # Add line items if available
        for item in receipt.line_items:
            writer.writerow([
                receipt.date.strftime('%m/%d/%Y') if receipt.date else receipt.created_at.strftime('%m/%d/%Y'),
                'Expense Detail',
                receipt.receipt_number or '',
                receipt.vendor or 'Unknown Vendor',
                item.description,
                f'Job Expenses:{item.category or "Materials"}',
                item.amount,
                '',
                f"Job {receipt.job.job_number}" if receipt.job else '',
                ''
            ])
    
    output.seek(0)
    return output.getvalue()

def export_job_summary_pdf(job):
    """Generate PDF summary report for a job"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Title
    story.append(Paragraph(f"Job Summary Report", title_style))
    story.append(Paragraph(f"Job #{job.job_number}", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    
    # Job details
    job_data = [
        ['Customer:', job.customer_name],
        ['Created:', job.created_at.strftime('%B %d, %Y')],
        ['Status:', job.status.title()],
        ['', ''],
        ['Original Quote:', f'${job.quoted_price:,.2f}' if job.quoted_price else 'N/A'],
        ['Current Costs:', f'${job.current_costs:,.2f}'],
        ['Profit/Loss:', f'${job.profit_amount:,.2f}'],
        ['Profit Margin:', f'{job.profit_margin:.1f}%']
    ]
    
    job_table = Table(job_data, colWidths=[2*inch, 3*inch])
    job_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 4), (1, -1), 'RIGHT'),
        ('TEXTCOLOR', (1, 6), (1, 6), colors.green if job.profit_amount > 0 else colors.red),
        ('LINEBELOW', (0, 3), (-1, 3), 1, colors.grey),
        ('TOPPADDING', (0, 4), (-1, 4), 12),
    ]))
    
    story.append(job_table)
    story.append(Spacer(1, 0.5*inch))
    
    # Receipts section
    story.append(Paragraph("Receipt Details", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    
    # Receipt table headers
    receipt_data = [['Date', 'Vendor', 'Receipt #', 'Amount']]
    
    # Add receipt rows
    for receipt in sorted(job.receipts, key=lambda r: r.created_at):
        receipt_data.append([
            receipt.date.strftime('%m/%d/%Y') if receipt.date else receipt.created_at.strftime('%m/%d/%Y'),
            receipt.vendor or 'Unknown',
            receipt.receipt_number or '-',
            f'${receipt.total:,.2f}' if receipt.total else '$0.00'
        ])
    
    # Add total row
    receipt_data.append(['', '', 'TOTAL:', f'${job.current_costs:,.2f}'])
    
    receipt_table = Table(receipt_data, colWidths=[1.5*inch, 3*inch, 1.5*inch, 1.5*inch])
    receipt_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -2), 'LEFT'),
        ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -2), 1, colors.black),
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ('BACKGROUND', (-2, -1), (-1, -1), colors.beige),
    ]))
    
    story.append(receipt_table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def export_receipts_zip(receipts, include_images=True):
    """Export receipts with images as ZIP file"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add CSV summary
        csv_data = export_receipts_csv(receipts)
        zip_file.writestr(f'receipts_export_{datetime.now().strftime("%Y%m%d")}.csv', csv_data)
        
        # Add images if requested
        if include_images:
            upload_folder = 'uploads'
            for receipt in receipts:
                if receipt.image_url and os.path.exists(os.path.join(upload_folder, receipt.image_url)):
                    image_path = os.path.join(upload_folder, receipt.image_url)
                    archive_name = f"receipts/{receipt.job.job_number if receipt.job else 'unassigned'}/{receipt.image_url}"
                    zip_file.write(image_path, archive_name)
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

def format_daily_summary_text(stats, insights):
    """Format daily summary for SMS/Email"""
    summary_lines = [
        f"Daily Summary - {datetime.now().strftime('%B %d, %Y')}",
        "=" * 40,
        ""
    ]
    
    # Overall stats
    summary_lines.extend([
        f"Active Jobs: {stats['total_jobs']}",
        f"Average Profit Margin: {stats['avg_profit_margin']}%",
        ""
    ])
    
    # Alerts
    if stats['jobs_over_budget'] > 0:
        summary_lines.extend([
            f"⚠️ ALERTS:",
            f"- {stats['jobs_over_budget']} jobs over budget",
            f"- Total loss this month: ${stats['money_lost_month']:,.2f}",
            ""
        ])
    
    # Problem patterns
    if insights:
        summary_lines.append("PROBLEM AREAS:")
        for insight in insights[:3]:  # Top 3 problem areas
            summary_lines.append(
                f"- {insight['keyword'].title()}: {insight['avg_margin']}% margin "
                f"({insight['losing_percentage']}% losing money)"
            )
        summary_lines.append("")
    
    # Cost alerts
    from insights import AlertMonitor
    alerts = AlertMonitor.check_cost_alerts()
    if alerts:
        summary_lines.append("JOBS APPROACHING BUDGET:")
        for alert in alerts[:3]:  # Top 3 alerts
            summary_lines.append(
                f"- Job #{alert['job_number']}: {alert['percentage']}% of budget used"
            )
    
    return "\n".join(summary_lines)