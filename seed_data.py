#!/usr/bin/env python3
"""
Seed script to populate the database with demo data
"""
import sys
import os
from datetime import datetime, timedelta
import random

# Add the backend directory to the path
sys.path.append(os.path.dirname(__file__))

from database import SessionLocal, User, Lead, Assignment, PreLead
from auth import get_password_hash

def create_demo_users(db):
    """Create demo users for testing"""
    users = [
        {
            "email": "admin@bonhoeffer.com",
            "password": "admin123",
            "full_name": "Admin User",
            "role": "admin"
        },
        {
            "email": "hr@bonhoeffer.com",
            "password": "hr123",
            "full_name": "HR Manager",
            "role": "hr"
        },
        {
            "email": "crm@bonhoeffer.com", 
            "password": "crm123",
            "full_name": "CRM Manager",
            "role": "crm"
        },
        {
            "email": "executive@bonhoeffer.com", 
            "password": "exec123",
            "full_name": "Executive Manager",
            "role": "executive"
        },
        {
            "email": "raj.kumar@bonhoeffer.com",
            "password": "raj123", 
            "full_name": "Raj Kumar",
            "role": "salesperson",
            "phone": "+91 98765 43210",
            "current_latitude": 28.6139,  # Delhi
            "current_longitude": 77.2090,
            "last_location_update": datetime.utcnow(),
            "territory": "Delhi"
        },
        {
            "email": "priya.sharma@bonhoeffer.com",
            "password": "priya123",
            "full_name": "Priya Sharma", 
            "role": "salesperson",
            "phone": "+91 98765 43211",
            "current_latitude": 19.0760,  # Mumbai
            "current_longitude": 72.8777,
            "last_location_update": datetime.utcnow(),
            "territory": "Maharashtra"
        },
        {
            "email": "amit.singh@bonhoeffer.com",
            "password": "amit123",
            "full_name": "Amit Singh",
            "role": "salesperson", 
            "phone": "+91 98765 43212",
            "current_latitude": 12.9716,  # Bangalore
            "current_longitude": 77.5946,
            "last_location_update": datetime.utcnow(),
            "territory": "Karnataka"
        },
        {
            "email": "sunita.devi@bonhoeffer.com",
            "password": "sunita123",
            "full_name": "Sunita Devi",
            "role": "salesperson",
            "phone": "+91 98765 43213", 
            "current_latitude": 22.5726,  # Kolkata
            "current_longitude": 88.3639,
            "last_location_update": datetime.utcnow(),
            "territory": "West Bengal"
        },
        {
            "email": "ravi.patel@bonhoeffer.com",
            "password": "ravi123",
            "full_name": "Ravi Patel",
            "role": "salesperson",
            "phone": "+91 98765 43214",
            "current_latitude": 23.0225,  # Ahmedabad
            "current_longitude": 72.5714,
            "last_location_update": datetime.utcnow(),
            "territory": "Gujarat"
        }
    ]
    
    created_users = []
    for user_data in users:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if existing_user:
            # Update existing user with territory if it's missing
            if hasattr(existing_user, 'territory') and existing_user.territory is None and user_data.get("territory"):
                existing_user.territory = user_data.get("territory")
                db.add(existing_user)
                print(f"Updated territory for existing user: {user_data['email']} -> {user_data.get('territory')}")
            else:
                print(f"User {user_data['email']} already exists, skipping...")
            created_users.append(existing_user)
            continue
            
        user = User(
            email=user_data["email"],
            hashed_password=get_password_hash(user_data["password"]),
            full_name=user_data["full_name"],
            role=user_data["role"],
            phone=user_data.get("phone"),
            current_latitude=user_data.get("current_latitude"),
            current_longitude=user_data.get("current_longitude"),
            last_location_update=user_data.get("last_location_update"),
            territory=user_data.get("territory")
        )
        db.add(user)
        created_users.append(user)
        print(f"Created user: {user_data['email']} (password: {user_data['password']})")
    
    db.commit()
    return created_users

def create_demo_leads(db):
    """Create demo leads across India"""
    leads_data = [
        {
            "company_name": "Tech Solutions Pvt Ltd",
            "contact_person": "Arun Mehta",
            "email": "arun@techsolutions.com",
            "phone": "+91 11 2345 6789",
            "address": "Connaught Place, New Delhi",
            "latitude": 28.6304,
            "longitude": 77.2177,
            "status": "new",
            "priority": "hot",
            "estimated_value": 500000.00,
            "notes": "Interested in industrial automation solutions"
        },
        {
            "company_name": "Mumbai Manufacturing Co",
            "contact_person": "Kavita Nair", 
            "email": "kavita@mumbaimanuf.com",
            "phone": "+91 22 9876 5432",
            "address": "Andheri East, Mumbai",
            "latitude": 19.1136,
            "longitude": 72.8697,
            "status": "contacted",
            "priority": "warm",
            "estimated_value": 750000.00,
            "notes": "Looking for packaging automation"
        },
        {
            "company_name": "Bangalore Tech Hub",
            "contact_person": "Suresh Reddy",
            "email": "suresh@blrtech.com", 
            "phone": "+91 80 1234 5678",
            "address": "Electronic City, Bangalore",
            "latitude": 12.8456,
            "longitude": 77.6603,
            "status": "new",
            "priority": "hot",
            "estimated_value": 1200000.00,
            "notes": "Enterprise automation project"
        },
        {
            "company_name": "Kolkata Industries",
            "contact_person": "Debasmita Roy",
            "email": "debasmita@kolind.com",
            "phone": "+91 33 8765 4321", 
            "address": "Salt Lake, Kolkata",
            "latitude": 22.5858,
            "longitude": 88.4026,
            "status": "qualified",
            "priority": "warm",
            "estimated_value": 300000.00,
            "notes": "Small scale automation requirements"
        },
        {
            "company_name": "Gujarat Heavy Industries",
            "contact_person": "Bhavesh Desai",
            "email": "bhavesh@gujarathi.com",
            "phone": "+91 79 5555 6666",
            "address": "GIDC Vatva, Ahmedabad", 
            "latitude": 23.0522,
            "longitude": 72.6311,
            "status": "new",
            "priority": "hot",
            "estimated_value": 2000000.00,
            "notes": "Large industrial automation project"
        },
        {
            "company_name": "Chennai Auto Parts",
            "contact_person": "Lakshmi Venkat",
            "email": "lakshmi@chennaiauto.com",
            "phone": "+91 44 7777 8888",
            "address": "Ambattur Industrial Estate, Chennai",
            "latitude": 13.1185,
            "longitude": 80.1574,
            "status": "contacted", 
            "priority": "warm",
            "estimated_value": 450000.00,
            "notes": "Automotive assembly line automation"
        },
        {
            "company_name": "Hyderabad Pharma Corp",
            "contact_person": "Dr. Ramesh Kumar",
            "email": "ramesh@hydpharma.com",
            "phone": "+91 40 9999 0000",
            "address": "Genome Valley, Hyderabad",
            "latitude": 17.4435,
            "longitude": 78.3772,
            "status": "proposal_sent",
            "priority": "hot",
            "estimated_value": 800000.00,
            "notes": "Pharmaceutical packaging automation"
        },
        {
            "company_name": "Pune Engineering Works",
            "contact_person": "Manoj Joshi",
            "email": "manoj@puneeng.com", 
            "phone": "+91 20 1111 2222",
            "address": "Pimpri-Chinchwad, Pune",
            "latitude": 18.6278,
            "longitude": 73.8131,
            "status": "new",
            "priority": "cold", 
            "estimated_value": 200000.00,
            "notes": "Basic automation requirements"
        }
    ]
    
    created_leads = []
    for lead_data in leads_data:
        # Check if lead already exists
        existing_lead = db.query(Lead).filter(Lead.email == lead_data["email"]).first()
        if existing_lead:
            print(f"Lead {lead_data['company_name']} already exists, skipping...")
            created_leads.append(existing_lead)
            continue
            
        lead = Lead(**lead_data)
        db.add(lead)
        created_leads.append(lead)
        print(f"Created lead: {lead_data['company_name']} in {lead_data['address']}")
    
    db.commit()
    return created_leads

def create_demo_assignments(db, users, leads):
    """Create some demo assignments"""
    salespeople = [u for u in users if u.role == "salesperson"]
    if not salespeople or not leads:
        print("No salespeople or leads available for assignments")
        return []
    
    # Create a few assignments
    assignments_data = [
        {
            "lead": leads[0],  # Delhi lead
            "salesperson": salespeople[0],  # Raj Kumar (Delhi)
            "status": "active",
            "notes": "Initial contact made, follow-up scheduled"
        },
        {
            "lead": leads[1],  # Mumbai lead  
            "salesperson": salespeople[1],  # Priya Sharma (Mumbai)
            "status": "completed",
            "notes": "Deal closed successfully"
        },
        {
            "lead": leads[2],  # Bangalore lead
            "salesperson": salespeople[2],  # Amit Singh (Bangalore) 
            "status": "active",
            "notes": "Technical presentation scheduled"
        }
    ]
    
    created_assignments = []
    for assignment_data in assignments_data:
        # Check if assignment already exists
        existing_assignment = db.query(Assignment).filter(
            Assignment.lead_id == assignment_data["lead"].id,
            Assignment.salesperson_id == assignment_data["salesperson"].id
        ).first()
        
        if existing_assignment:
            print(f"Assignment for {assignment_data['lead'].company_name} already exists, skipping...")
            created_assignments.append(existing_assignment)
            continue
            
        assignment = Assignment(
            lead_id=assignment_data["lead"].id,
            salesperson_id=assignment_data["salesperson"].id,
            status=assignment_data["status"],
            notes=assignment_data["notes"]
        )
        db.add(assignment)
        created_assignments.append(assignment)
        print(f"Created assignment: {assignment_data['lead'].company_name} -> {assignment_data['salesperson'].full_name}")
    
    db.commit()
    return created_assignments

def create_demo_preleads(db, users):
    """Create demo pre-leads for testing"""
    # Get CRM user for created_by field
    crm_user = next((user for user in users if user.role == 'crm'), users[0])
    
    preleads_data = [
        {
            "company_name": "Global Tech Industries",
            "country": "India",
            "reason": "Expanding manufacturing operations, need automation solutions",
            "source": "trade_show",
            "classification": "hot",
            "notes": "Met at Industrial Automation Expo 2025, very interested in our robotic solutions"
        },
        {
            "company_name": "European Manufacturing Solutions",
            "country": "Germany",
            "reason": "Digitization of legacy manufacturing systems",
            "source": "referral",
            "classification": "warm",
            "notes": "Referred by existing client, scheduled for initial call next week"
        },
        {
            "company_name": "Asia Pacific Textiles",
            "country": "Bangladesh",
            "reason": "Modernizing textile production line",
            "source": "website",
            "classification": "cold",
            "notes": "Filled contact form on website, requested product brochure"
        },
        {
            "company_name": "Nordic Engineering AB",
            "country": "Sweden",
            "reason": "Green energy integration with manufacturing",
            "source": "linkedin",
            "classification": "warm",
            "notes": "Connected via LinkedIn, interested in sustainable automation solutions"
        },
        {
            "company_name": "Middle East Industrial Corp",
            "country": "UAE",
            "reason": "Setting up new facility, need complete automation",
            "source": "cold_call",
            "classification": "hot",
            "notes": "Urgent requirement, budget approved, decision expected within 2 weeks"
        },
        {
            "company_name": "South American Metals Ltd",
            "country": "Brazil",
            "reason": "Upgrading mining equipment automation",
            "source": "trade_show",
            "classification": "warm",
            "notes": "Met at Mining Technology Conference, interested in our control systems"
        },
        {
            "company_name": "African Processing Solutions",
            "country": "South Africa",
            "reason": "Food processing automation upgrade",
            "source": "email_campaign",
            "classification": "cold",
            "notes": "Responded to our email campaign, requested technical specifications"
        },
        {
            "company_name": "Pacific Manufacturing Inc",
            "country": "Australia",
            "reason": "Smart factory implementation",
            "source": "referral",
            "classification": "hot",
            "notes": "Referred by local partner, ready to move forward quickly"
        }
    ]
    
    created_preleads = []
    for prelead_data in preleads_data:
        # Check if pre-lead already exists
        existing_prelead = db.query(PreLead).filter(
            PreLead.company_name == prelead_data["company_name"]
        ).first()
        if existing_prelead:
            print(f"Pre-lead {prelead_data['company_name']} already exists, skipping...")
            created_preleads.append(existing_prelead)
            continue
            
        prelead = PreLead(
            company_name=prelead_data["company_name"],
            country=prelead_data["country"],
            reason=prelead_data["reason"],
            source=prelead_data["source"],
            classification=prelead_data["classification"],
            notes=prelead_data["notes"],
            created_by=crm_user.id
        )
        db.add(prelead)
        created_preleads.append(prelead)
        print(f"Created pre-lead: {prelead_data['company_name']} ({prelead_data['country']})")
    
    db.commit()
    return created_preleads

def main():
    """Main seeding function"""
    print("🌱 Seeding database with demo data...")
    
    db = SessionLocal()
    try:
        # Create demo users
        print("\n👥 Creating demo users...")
        users = create_demo_users(db)
        
        # Create demo leads
        print("\n🎯 Creating demo leads...")
        leads = create_demo_leads(db)
        
        # Create demo pre-leads
        print("\n🔥 Creating demo pre-leads...")
        preleads = create_demo_preleads(db, users)
        
        # Create demo assignments
        print("\n📋 Creating demo assignments...")
        assignments = create_demo_assignments(db, users, leads)
        
        print(f"\n✅ Database seeded successfully!")
        print(f"   - Created {len(users)} users")
        print(f"   - Created {len(leads)} leads")
        print(f"   - Created {len(preleads)} pre-leads")
        print(f"   - Created {len(assignments)} assignments")
        
        print("\n🔑 Demo login credentials:")
        print("   Admin: admin@bonhoeffer.com / admin123")
        print("   CRM: crm@bonhoeffer.com / crm123")
        print("   Salesperson (Raj): raj.kumar@bonhoeffer.com / raj123")
        print("   Salesperson (Priya): priya.sharma@bonhoeffer.com / priya123")
        print("   Salesperson (Amit): amit.singh@bonhoeffer.com / amit123")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
