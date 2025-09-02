"""
Comprehensive job risk seed data based on Anthropic study methodology.
Contains 100+ job titles with base automation/augmentation scores.
"""

JOB_TITLES_DATA = {
    # HIGH RISK JOBS (Automation Risk > 60%)
    
    # Technology & Development
    "software developer": {"automation_risk": 65.0, "augmentation_potential": 35.0, "category": "technology"},
    "web developer": {"automation_risk": 70.0, "augmentation_potential": 30.0, "category": "technology"},
    "frontend developer": {"automation_risk": 68.0, "augmentation_potential": 32.0, "category": "technology"},
    "backend developer": {"automation_risk": 62.0, "augmentation_potential": 38.0, "category": "technology"},
    "mobile app developer": {"automation_risk": 67.0, "augmentation_potential": 33.0, "category": "technology"},
    "data scientist": {"automation_risk": 55.0, "augmentation_potential": 45.0, "category": "technology"},
    "machine learning engineer": {"automation_risk": 50.0, "augmentation_potential": 50.0, "category": "technology"},
    "devops engineer": {"automation_risk": 60.0, "augmentation_potential": 40.0, "category": "technology"},
    "qa engineer": {"automation_risk": 75.0, "augmentation_potential": 25.0, "category": "technology"},
    "system administrator": {"automation_risk": 70.0, "augmentation_potential": 30.0, "category": "technology"},
    
    # Content & Creative
    "content writer": {"automation_risk": 60.0, "augmentation_potential": 35.0, "category": "creative"},
    "copywriter": {"automation_risk": 65.0, "augmentation_potential": 30.0, "category": "creative"},
    "technical writer": {"automation_risk": 70.0, "augmentation_potential": 25.0, "category": "creative"},
    "blogger": {"automation_risk": 75.0, "augmentation_potential": 20.0, "category": "creative"},
    "social media manager": {"automation_risk": 65.0, "augmentation_potential": 30.0, "category": "marketing"},
    "seo specialist": {"automation_risk": 80.0, "augmentation_potential": 15.0, "category": "marketing"},
    "translator": {"automation_risk": 75.0, "augmentation_potential": 25.0, "category": "language"},
    "interpreter": {"automation_risk": 70.0, "augmentation_potential": 30.0, "category": "language"},
    "editor": {"automation_risk": 55.0, "augmentation_potential": 40.0, "category": "creative"},
    "proofreader": {"automation_risk": 85.0, "augmentation_potential": 10.0, "category": "creative"},
    
    # Administrative & Support
    "data entry clerk": {"automation_risk": 85.0, "augmentation_potential": 15.0, "category": "administrative"},
    "administrative assistant": {"automation_risk": 75.0, "augmentation_potential": 25.0, "category": "administrative"},
    "receptionist": {"automation_risk": 80.0, "augmentation_potential": 20.0, "category": "administrative"},
    "office manager": {"automation_risk": 60.0, "augmentation_potential": 35.0, "category": "administrative"},
    "executive assistant": {"automation_risk": 55.0, "augmentation_potential": 40.0, "category": "administrative"},
    "virtual assistant": {"automation_risk": 90.0, "augmentation_potential": 10.0, "category": "administrative"},
    "scheduler": {"automation_risk": 85.0, "augmentation_potential": 15.0, "category": "administrative"},
    "coordinator": {"automation_risk": 70.0, "augmentation_potential": 30.0, "category": "administrative"},
    
    # Customer Service
    "customer service representative": {"automation_risk": 70.0, "augmentation_potential": 30.0, "category": "service"},
    "call center agent": {"automation_risk": 80.0, "augmentation_potential": 20.0, "category": "service"},
    "customer support specialist": {"automation_risk": 65.0, "augmentation_potential": 35.0, "category": "service"},
    "help desk technician": {"automation_risk": 75.0, "augmentation_potential": 25.0, "category": "service"},
    "technical support specialist": {"automation_risk": 70.0, "augmentation_potential": 30.0, "category": "service"},
    
    # Finance & Accounting
    "bookkeeper": {"automation_risk": 80.0, "augmentation_potential": 20.0, "category": "finance"},
    "accountant": {"automation_risk": 65.0, "augmentation_potential": 30.0, "category": "finance"},
    "accounts payable clerk": {"automation_risk": 85.0, "augmentation_potential": 15.0, "category": "finance"},
    "accounts receivable clerk": {"automation_risk": 85.0, "augmentation_potential": 15.0, "category": "finance"},
    "payroll specialist": {"automation_risk": 80.0, "augmentation_potential": 20.0, "category": "finance"},
    "tax preparer": {"automation_risk": 75.0, "augmentation_potential": 25.0, "category": "finance"},
    "auditor": {"automation_risk": 60.0, "augmentation_potential": 35.0, "category": "finance"},
    
    # Sales & Retail
    "retail sales associate": {"automation_risk": 75.0, "augmentation_potential": 25.0, "category": "retail"},
    "cashier": {"automation_risk": 90.0, "augmentation_potential": 10.0, "category": "retail"},
    "sales clerk": {"automation_risk": 70.0, "augmentation_potential": 30.0, "category": "retail"},
    "telemarketer": {"automation_risk": 85.0, "augmentation_potential": 15.0, "category": "sales"},
    "inside sales representative": {"automation_risk": 70.0, "augmentation_potential": 30.0, "category": "sales"},
    
    # Manufacturing & Production
    "assembly line worker": {"automation_risk": 95.0, "augmentation_potential": 5.0, "category": "manufacturing"},
    "machine operator": {"automation_risk": 90.0, "augmentation_potential": 10.0, "category": "manufacturing"},
    "production worker": {"automation_risk": 85.0, "augmentation_potential": 15.0, "category": "manufacturing"},
    "quality control inspector": {"automation_risk": 80.0, "augmentation_potential": 20.0, "category": "manufacturing"},
    "warehouse worker": {"automation_risk": 85.0, "augmentation_potential": 15.0, "category": "logistics"},
    "forklift operator": {"automation_risk": 80.0, "augmentation_potential": 20.0, "category": "logistics"},
    
    # MEDIUM RISK JOBS (Automation Risk 30-60%)
    
    # Management & Leadership
    "project manager": {"automation_risk": 40.0, "augmentation_potential": 55.0, "category": "management"},
    "marketing manager": {"automation_risk": 35.0, "augmentation_potential": 50.0, "category": "marketing"},
    "product manager": {"automation_risk": 30.0, "augmentation_potential": 60.0, "category": "management"},
    "operations manager": {"automation_risk": 45.0, "augmentation_potential": 45.0, "category": "management"},
    "sales manager": {"automation_risk": 40.0, "augmentation_potential": 50.0, "category": "sales"},
    "team lead": {"automation_risk": 35.0, "augmentation_potential": 55.0, "category": "management"},
    "department manager": {"automation_risk": 30.0, "augmentation_potential": 60.0, "category": "management"},
    
    # Finance & Analysis
    "financial analyst": {"automation_risk": 45.0, "augmentation_potential": 45.0, "category": "finance"},
    "business analyst": {"automation_risk": 40.0, "augmentation_potential": 50.0, "category": "analysis"},
    "data analyst": {"automation_risk": 50.0, "augmentation_potential": 40.0, "category": "analysis"},
    "market research analyst": {"automation_risk": 45.0, "augmentation_potential": 45.0, "category": "research"},
    "investment analyst": {"automation_risk": 40.0, "augmentation_potential": 50.0, "category": "finance"},
    "credit analyst": {"automation_risk": 55.0, "augmentation_potential": 35.0, "category": "finance"},
    "risk analyst": {"automation_risk": 45.0, "augmentation_potential": 45.0, "category": "finance"},
    
    # Sales & Business Development
    "sales representative": {"automation_risk": 50.0, "augmentation_potential": 40.0, "category": "sales"},
    "account executive": {"automation_risk": 45.0, "augmentation_potential": 45.0, "category": "sales"},
    "business development representative": {"automation_risk": 50.0, "augmentation_potential": 40.0, "category": "sales"},
    "sales consultant": {"automation_risk": 40.0, "augmentation_potential": 50.0, "category": "sales"},
    "relationship manager": {"automation_risk": 35.0, "augmentation_potential": 55.0, "category": "sales"},
    
    # Human Resources
    "human resources specialist": {"automation_risk": 55.0, "augmentation_potential": 35.0, "category": "hr"},
    "recruiter": {"automation_risk": 60.0, "augmentation_potential": 30.0, "category": "hr"},
    "hr coordinator": {"automation_risk": 65.0, "augmentation_potential": 25.0, "category": "hr"},
    "talent acquisition specialist": {"automation_risk": 55.0, "augmentation_potential": 35.0, "category": "hr"},
    "compensation analyst": {"automation_risk": 50.0, "augmentation_potential": 40.0, "category": "hr"},
    
    # Research & Analysis
    "researcher": {"automation_risk": 30.0, "augmentation_potential": 60.0, "category": "research"},
    "market researcher": {"automation_risk": 40.0, "augmentation_potential": 50.0, "category": "research"},
    "policy analyst": {"automation_risk": 35.0, "augmentation_potential": 55.0, "category": "research"},
    "intelligence analyst": {"automation_risk": 45.0, "augmentation_potential": 45.0, "category": "research"},
    "competitive analyst": {"automation_risk": 40.0, "augmentation_potential": 50.0, "category": "research"},
    
    # Creative & Design
    "graphic designer": {"automation_risk": 35.0, "augmentation_potential": 55.0, "category": "creative"},
    "ui designer": {"automation_risk": 30.0, "augmentation_potential": 60.0, "category": "creative"},
    "ux designer": {"automation_risk": 25.0, "augmentation_potential": 65.0, "category": "creative"},
    "web designer": {"automation_risk": 40.0, "augmentation_potential": 50.0, "category": "creative"},
    "illustrator": {"automation_risk": 30.0, "augmentation_potential": 60.0, "category": "creative"},
    "photographer": {"automation_risk": 25.0, "augmentation_potential": 65.0, "category": "creative"},
    "videographer": {"automation_risk": 30.0, "augmentation_potential": 60.0, "category": "creative"},
    
    # Healthcare Support
    "medical assistant": {"automation_risk": 55.0, "augmentation_potential": 35.0, "category": "healthcare"},
    "pharmacy technician": {"automation_risk": 60.0, "augmentation_potential": 30.0, "category": "healthcare"},
    "dental assistant": {"automation_risk": 50.0, "augmentation_potential": 40.0, "category": "healthcare"},
    "medical coder": {"automation_risk": 70.0, "augmentation_potential": 25.0, "category": "healthcare"},
    "healthcare administrator": {"automation_risk": 45.0, "augmentation_potential": 45.0, "category": "healthcare"},
    
    # Legal Support
    "paralegal": {"automation_risk": 55.0, "augmentation_potential": 35.0, "category": "legal"},
    "legal assistant": {"automation_risk": 60.0, "augmentation_potential": 30.0, "category": "legal"},
    "compliance specialist": {"automation_risk": 50.0, "augmentation_potential": 40.0, "category": "legal"},
    "contract specialist": {"automation_risk": 55.0, "augmentation_potential": 35.0, "category": "legal"},
    
    # LOW RISK JOBS (Automation Risk < 30%)
    
    # Education & Training
    "teacher": {"automation_risk": 15.0, "augmentation_potential": 60.0, "category": "education"},
    "professor": {"automation_risk": 10.0, "augmentation_potential": 65.0, "category": "education"},
    "trainer": {"automation_risk": 20.0, "augmentation_potential": 55.0, "category": "education"},
    "instructional designer": {"automation_risk": 25.0, "augmentation_potential": 60.0, "category": "education"},
    "curriculum developer": {"automation_risk": 20.0, "augmentation_potential": 65.0, "category": "education"},
    "academic advisor": {"automation_risk": 15.0, "augmentation_potential": 60.0, "category": "education"},
    
    # Healthcare & Therapy
    "therapist": {"automation_risk": 5.0, "augmentation_potential": 45.0, "category": "healthcare"},
    "psychologist": {"automation_risk": 5.0, "augmentation_potential": 50.0, "category": "healthcare"},
    "counselor": {"automation_risk": 10.0, "augmentation_potential": 45.0, "category": "healthcare"},
    "nurse": {"automation_risk": 25.0, "augmentation_potential": 55.0, "category": "healthcare"},
    "nurse practitioner": {"automation_risk": 15.0, "augmentation_potential": 60.0, "category": "healthcare"},
    "physician": {"automation_risk": 10.0, "augmentation_potential": 65.0, "category": "healthcare"},
    "surgeon": {"automation_risk": 5.0, "augmentation_potential": 70.0, "category": "healthcare"},
    "physical therapist": {"automation_risk": 15.0, "augmentation_potential": 55.0, "category": "healthcare"},
    "occupational therapist": {"automation_risk": 15.0, "augmentation_potential": 55.0, "category": "healthcare"},
    "speech therapist": {"automation_risk": 20.0, "augmentation_potential": 50.0, "category": "healthcare"},
    
    # Legal & Consulting
    "lawyer": {"automation_risk": 30.0, "augmentation_potential": 50.0, "category": "legal"},
    "attorney": {"automation_risk": 25.0, "augmentation_potential": 55.0, "category": "legal"},
    "consultant": {"automation_risk": 20.0, "augmentation_potential": 58.0, "category": "consulting"},
    "management consultant": {"automation_risk": 15.0, "augmentation_potential": 65.0, "category": "consulting"},
    "strategy consultant": {"automation_risk": 10.0, "augmentation_potential": 70.0, "category": "consulting"},
    "business consultant": {"automation_risk": 20.0, "augmentation_potential": 60.0, "category": "consulting"},
    
    # Creative & Arts
    "artist": {"automation_risk": 10.0, "augmentation_potential": 55.0, "category": "creative"},
    "musician": {"automation_risk": 15.0, "augmentation_potential": 50.0, "category": "creative"},
    "writer": {"automation_risk": 20.0, "augmentation_potential": 55.0, "category": "creative"},
    "journalist": {"automation_risk": 25.0, "augmentation_potential": 50.0, "category": "creative"},
    "filmmaker": {"automation_risk": 15.0, "augmentation_potential": 60.0, "category": "creative"},
    "actor": {"automation_risk": 5.0, "augmentation_potential": 45.0, "category": "creative"},
    "director": {"automation_risk": 10.0, "augmentation_potential": 65.0, "category": "creative"},
    
    # Leadership & Executive
    "ceo": {"automation_risk": 5.0, "augmentation_potential": 70.0, "category": "executive"},
    "executive": {"automation_risk": 10.0, "augmentation_potential": 65.0, "category": "executive"},
    "director": {"automation_risk": 15.0, "augmentation_potential": 60.0, "category": "executive"},
    "vice president": {"automation_risk": 10.0, "augmentation_potential": 65.0, "category": "executive"},
    "chief officer": {"automation_risk": 5.0, "augmentation_potential": 70.0, "category": "executive"},
    
    # Social Services
    "social worker": {"automation_risk": 15.0, "augmentation_potential": 50.0, "category": "social_services"},
    "case manager": {"automation_risk": 20.0, "augmentation_potential": 45.0, "category": "social_services"},
    "community organizer": {"automation_risk": 10.0, "augmentation_potential": 55.0, "category": "social_services"},
    "nonprofit director": {"automation_risk": 15.0, "augmentation_potential": 60.0, "category": "social_services"},
    
    # Skilled Trades
    "electrician": {"automation_risk": 25.0, "augmentation_potential": 50.0, "category": "trades"},
    "plumber": {"automation_risk": 20.0, "augmentation_potential": 45.0, "category": "trades"},
    "carpenter": {"automation_risk": 25.0, "augmentation_potential": 45.0, "category": "trades"},
    "mechanic": {"automation_risk": 30.0, "augmentation_potential": 40.0, "category": "trades"},
    "technician": {"automation_risk": 35.0, "augmentation_potential": 45.0, "category": "trades"},
    
    # Hospitality & Service
    "chef": {"automation_risk": 20.0, "augmentation_potential": 50.0, "category": "hospitality"},
    "restaurant manager": {"automation_risk": 25.0, "augmentation_potential": 55.0, "category": "hospitality"},
    "hotel manager": {"automation_risk": 20.0, "augmentation_potential": 60.0, "category": "hospitality"},
    "event planner": {"automation_risk": 25.0, "augmentation_potential": 55.0, "category": "hospitality"},
    "concierge": {"automation_risk": 30.0, "augmentation_potential": 45.0, "category": "hospitality"},
    
    # Government & Public Service
    "policy maker": {"automation_risk": 15.0, "augmentation_potential": 60.0, "category": "government"},
    "diplomat": {"automation_risk": 10.0, "augmentation_potential": 65.0, "category": "government"},
    "public administrator": {"automation_risk": 20.0, "augmentation_potential": 55.0, "category": "government"},
    "legislator": {"automation_risk": 5.0, "augmentation_potential": 70.0, "category": "government"},
    
    # Emergency Services
    "firefighter": {"automation_risk": 15.0, "augmentation_potential": 50.0, "category": "emergency"},
    "police officer": {"automation_risk": 20.0, "augmentation_potential": 45.0, "category": "emergency"},
    "paramedic": {"automation_risk": 25.0, "augmentation_potential": 50.0, "category": "emergency"},
    "emergency dispatcher": {"automation_risk": 30.0, "augmentation_potential": 40.0, "category": "emergency"}
}

# Industry modifiers for risk calculation
INDUSTRY_MODIFIERS = {
    "technology": 1.2,      # Higher automation due to tech adoption
    "finance": 1.1,         # Moderate automation in financial services
    "healthcare": 0.8,      # Lower automation due to human care requirements
    "education": 0.7,       # Lower automation due to human interaction
    "retail": 1.3,          # Higher automation in retail operations
    "manufacturing": 1.4,   # High automation in manufacturing
    "consulting": 0.9,      # Lower automation due to strategic thinking
    "marketing": 1.0,       # Neutral automation potential
    "legal": 0.8,           # Lower automation due to legal complexity
    "government": 0.6,      # Lower automation due to bureaucratic processes
    "nonprofit": 0.7,       # Lower automation due to mission-driven work
    "media": 1.1,           # Moderate automation in content creation
    "real estate": 0.9,     # Lower automation due to relationship building
    "hospitality": 1.2,     # Higher automation in service delivery
    "transportation": 1.3,  # Higher automation in logistics
    "construction": 1.1,    # Moderate automation in construction
    "energy": 1.0,          # Neutral automation potential
    "agriculture": 1.2,     # Higher automation in agriculture
    "pharmaceuticals": 1.0, # Neutral automation potential
    "aerospace": 1.1        # Moderate automation in aerospace
}

# Task risk mappings
TASK_RISK_MAPPINGS = {
    "data_entry": {"automation_probability": 85.0, "augmentation_potential": 15.0, "description": "Repetitive data input tasks"},
    "customer_service": {"automation_probability": 70.0, "augmentation_potential": 30.0, "description": "Customer interaction and support"},
    "content_creation": {"automation_probability": 60.0, "augmentation_potential": 35.0, "description": "Creating written or visual content"},
    "analysis": {"automation_probability": 45.0, "augmentation_potential": 50.0, "description": "Data analysis and interpretation"},
    "coding": {"automation_probability": 65.0, "augmentation_potential": 30.0, "description": "Software development and programming"},
    "design": {"automation_probability": 25.0, "augmentation_potential": 55.0, "description": "Creative design and visual work"},
    "management": {"automation_probability": 20.0, "augmentation_potential": 60.0, "description": "Team leadership and coordination"},
    "research": {"automation_probability": 30.0, "augmentation_potential": 60.0, "description": "Information gathering and analysis"},
    "planning": {"automation_probability": 35.0, "augmentation_potential": 55.0, "description": "Strategic planning and coordination"},
    "communication": {"automation_probability": 40.0, "augmentation_potential": 50.0, "description": "Internal and external communication"},
    "training": {"automation_probability": 25.0, "augmentation_potential": 60.0, "description": "Training and development activities"},
    "sales": {"automation_probability": 50.0, "augmentation_potential": 40.0, "description": "Sales and business development"},
    "accounting": {"automation_probability": 75.0, "augmentation_potential": 20.0, "description": "Financial accounting and bookkeeping"},
    "quality_control": {"automation_probability": 70.0, "augmentation_potential": 25.0, "description": "Quality assurance and testing"},
    "maintenance": {"automation_probability": 60.0, "augmentation_potential": 35.0, "description": "Equipment and system maintenance"}
}
