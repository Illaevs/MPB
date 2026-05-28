"""
Quick fix: Add our_company_id to Deal model
Run this once to update the model file
"""
import re

# Read the file
with open('app/models/deal.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add our_company_id after customer_id if not already present
if 'our_company_id' not in content:
    content = content.replace(
        '    customer_id = Column(String(36), ForeignKey("companies.id"))',
        '    customer_id = Column(String(36), ForeignKey("companies.id"))\n    our_company_id = Column(String(36), ForeignKey("companies.id"))'
    )
    
    # Write back
    with open('app/models/deal.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ Added our_company_id column to Deal model")
else:
    print("✓ our_company_id already exists in Deal model")
