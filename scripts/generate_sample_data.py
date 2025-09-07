"""
Sample data generator for testing the profit tracking dashboard.
Generates realistic jobs with various profit margins and receipts.
"""

import random
from datetime import datetime, timedelta
from app import app, db
from models import Job, Receipt, LineItem
import json

# Sample data configurations
JOB_TYPES = [
    {'category': 'Plumbing', 'customers': ['Johnson Plumbing', 'Quick Fix Plumbing', 'Davis Water Works', 'Smith Pipe Repair'], 
     'typical_quote': (500, 5000), 'margin_range': (-20, 35)},
    {'category': 'Electrical', 'customers': ['Bright Electric', 'PowerUp Solutions', 'Wilson Wiring', 'Lightning Electric'], 
     'typical_quote': (800, 8000), 'margin_range': (5, 40)},
    {'category': 'HVAC', 'customers': ['Cool Air Services', 'Heat & Cool Pro', 'Climate Control Inc', 'Comfort Zone HVAC'], 
     'typical_quote': (1500, 12000), 'margin_range': (10, 45)},
    {'category': 'Roofing', 'customers': ['Top Roof Repairs', 'Shelter Pro Roofing', 'Peak Performance Roofing', 'Sky High Roofing'], 
     'typical_quote': (3000, 25000), 'margin_range': (15, 50)},
    {'category': 'General', 'customers': ['ABC Construction', 'BuildRight Co', 'Quality Contractors', 'Premier Building'], 
     'typical_quote': (1000, 10000), 'margin_range': (-10, 30)}
]

VENDORS = [
    'Home Depot', 'Lowes', 'Ferguson', 'Grainger', 'Menards', 
    'Ace Hardware', 'True Value', 'Local Supply Co', 'ProBuild', 
    'Contractor Supply', 'Industrial Supply', 'Wholesale Electric'
]

RECEIPT_ITEMS = {
    'Plumbing': [
        ('PVC Pipe 2"', 15.99), ('Copper Fitting', 8.50), ('Shut-off Valve', 24.99),
        ('Toilet Flange', 12.99), ('Wax Ring', 4.99), ('Supply Line', 9.99),
        ('P-Trap', 18.99), ('Pipe Cement', 6.99), ('Teflon Tape', 3.99)
    ],
    'Electrical': [
        ('12/2 Romex Wire 250ft', 89.99), ('20A Breaker', 12.99), ('Outlet Box', 2.99),
        ('GFCI Outlet', 18.99), ('Wire Nuts', 8.99), ('Junction Box', 4.99),
        ('Light Switch', 3.99), ('Electrical Tape', 4.99), ('Conduit 10ft', 14.99)
    ],
    'HVAC': [
        ('Air Filter 20x25', 24.99), ('Thermostat', 149.99), ('Refrigerant', 89.99),
        ('Capacitor', 45.99), ('Blower Motor', 189.99), ('Duct Tape', 12.99),
        ('Flex Duct 25ft', 65.99), ('Register Vent', 15.99), ('Insulation', 34.99)
    ],
    'Roofing': [
        ('Shingles Bundle', 34.99), ('Roofing Felt', 24.99), ('Flashing', 18.99),
        ('Roofing Nails 5lb', 14.99), ('Ridge Vent', 45.99), ('Drip Edge 10ft', 12.99),
        ('Sealant Tube', 8.99), ('Gutter 10ft', 28.99), ('Downspout', 15.99)
    ],
    'General': [
        ('2x4 Lumber', 8.99), ('Plywood Sheet', 45.99), ('Concrete Bag', 7.99),
        ('Screws Box', 12.99), ('Paint Gallon', 34.99), ('Brush Set', 14.99),
        ('Drop Cloth', 9.99), ('Safety Glasses', 6.99), ('Work Gloves', 8.99)
    ]
}

def generate_sample_data():
    """Generate sample jobs and receipts"""
    with app.app_context():
        print("Generating sample data...")
        
        # Start job numbers from 2001 to avoid conflicts with test data
        job_number = 2001
        
        for i in range(20):
            # Select random job type
            job_type = random.choice(JOB_TYPES)
            customer = random.choice(job_type['customers'])
            
            # Generate quote
            quote_min, quote_max = job_type['typical_quote']
            quoted_price = random.uniform(quote_min, quote_max)
            
            # Determine target margin
            margin_min, margin_max = job_type['margin_range']
            target_margin = random.uniform(margin_min, margin_max)
            
            # Calculate target costs based on margin
            target_costs = quoted_price * (1 - target_margin / 100)
            
            # Create job
            job = Job(
                job_number=str(job_number),
                customer_name=customer,
                quoted_price=quoted_price,
                created_at=datetime.now() - timedelta(days=random.randint(1, 60))
            )
            db.session.add(job)
            db.session.commit()
            
            # Generate receipts to reach target costs (with some randomness)
            current_costs = 0
            receipt_count = random.randint(2, 8)
            
            for j in range(receipt_count):
                # Don't exceed target by too much
                if current_costs >= target_costs * 1.1:
                    break
                
                # Generate receipt amount
                avg_receipt = target_costs / receipt_count
                receipt_total = random.uniform(avg_receipt * 0.5, avg_receipt * 1.5)
                
                # Create receipt
                receipt = Receipt(
                    image_url=f"sample_{job_number}_{j}.jpg",
                    vendor=random.choice(VENDORS),
                    total=receipt_total,
                    date=(job.created_at + timedelta(days=random.randint(0, 30))).date(),
                    receipt_number=f"R{random.randint(100000, 999999)}",
                    job_id=job.id,
                    uploaded_by="Sample Generator",
                    upload_method='web',
                    extracted_data={'sample': True},
                    created_at=job.created_at + timedelta(days=random.randint(0, 30))
                )
                db.session.add(receipt)
                db.session.commit()
                
                # Add line items
                category = job_type['category']
                items = random.sample(RECEIPT_ITEMS[category], k=random.randint(1, 4))
                
                # Adjust item prices to match receipt total
                item_total = sum(item[1] for item in items)
                scale_factor = receipt_total / item_total if item_total > 0 else 1
                
                for item_name, base_price in items:
                    line_item = LineItem(
                        receipt_id=receipt.id,
                        description=item_name,
                        amount=base_price * scale_factor,
                        category=category
                    )
                    db.session.add(line_item)
                
                current_costs += receipt_total
            
            db.session.commit()
            
            # Print job summary
            actual_margin = ((quoted_price - current_costs) / quoted_price * 100) if quoted_price > 0 else 0
            print(f"Job #{job_number} - {customer}: Quote ${quoted_price:.2f}, "
                  f"Costs ${current_costs:.2f}, Margin {actual_margin:.1f}%")
            
            job_number += 1
        
        print("\nSample data generation complete!")
        print(f"Created 20 jobs with receipts")
        
        # Generate daily summary
        from analytics import generate_daily_summary
        summary = generate_daily_summary()
        print("\n" + "="*50)
        print("DAILY SUMMARY:")
        print("="*50)
        print(summary)

if __name__ == "__main__":
    generate_sample_data()