from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import os
import uuid
from pathlib import Path
import shutil
import requests
import re

import schemas
from database import get_db, User, Lead, Assignment, PreLead, engine, Base
from auth import (
    authenticate_user, create_access_token, get_current_active_user,
    get_password_hash, get_user_by_email
)
from utils import sort_salespeople_by_distance
from config import settings

app = FastAPI(title="Bonhoeffer Machines CRM API", version="1.0.0")

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    """Initialize database and seed data if needed"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified")
        
        # Check if we need to seed data
        db = next(get_db())
        try:
            user_count = db.query(User).count()
            if user_count == 0:
                print("🌱 No users found. Seeding initial data...")
                # Import and run seed function
                from seed_data import main as seed_main
                seed_main()
                print("✅ Initial data seeded successfully!")
            else:
                print(f"👥 Found {user_count} users. Database already initialized.")
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        # Don't fail the startup, but log the error
        import traceback
        traceback.print_exc()

# Create uploads directory if it doesn't exist
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)

# Mount static files for uploaded images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint for Render
@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}

# Seed database endpoint (for manual seeding if needed)
@app.post("/seed-database")
async def seed_database(db: Session = Depends(get_db)):
    """Manually seed the database with initial data"""
    try:
        user_count = db.query(User).count()
        if user_count > 0:
            return {"message": f"Database already has {user_count} users. Skipping seed."}
        
        # Import and run seed function
        from seed_data import main as seed_main
        seed_main()
        
        # Verify seeding worked
        new_user_count = db.query(User).count()
        return {
            "message": "Database seeded successfully!",
            "users_created": new_user_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to seed database: {str(e)}"
        )

# Auth endpoints
@app.post("/login", response_model=schemas.Token)
async def login(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=schemas.User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.post("/resolve-url")
async def resolve_url(url_data: dict):
    """
    Resolve shortened URLs to extract coordinates from Google Maps links
    This endpoint handles the URL resolution server-side to avoid CORS issues
    """
    url = url_data.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    try:
        # Check if it's a shortened URL that needs resolution
        if any(domain in url for domain in ['maps.app.goo.gl', 'goo.gl/maps', 'bit.ly', 'tinyurl.com']):
            # Resolve the shortened URL
            response = requests.head(url, allow_redirects=True, timeout=10)
            resolved_url = response.url
        else:
            resolved_url = url
        
        # Extract coordinates using enhanced patterns
        patterns = [
            r'@(-?\d+\.?\d*),(-?\d+\.?\d*)',
            r'll=(-?\d+\.?\d*),(-?\d+\.?\d*)',
            r'q=(-?\d+\.?\d*),(-?\d+\.?\d*)',
            r'!3d(-?\d+\.?\d*)!4d(-?\d+\.?\d*)',
            r'data=.*?(-?\d+\.?\d*),(-?\d+\.?\d*)',
            r'(-?\d+\.\d{4,}),(-?\d+\.\d{4,})',
            r'(-?\d{1,3}\.\d+),(-?\d{1,3}\.\d+)',
            # Handle /search/ URLs with coordinates like: /search/26.851325,+79.746548
            r'/search/(-?\d+\.?\d*),\+?(-?\d+\.?\d*)',
            # Handle URLs with coordinates followed by comma and space/plus
            r'(-?\d+\.?\d*),\s*\+?(-?\d+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, resolved_url)
            if match:
                lat = float(match.group(1))
                lng = float(match.group(2))
                
                if -90 <= lat <= 90 and -180 <= lng <= 180:
                    return {
                        "success": True,
                        "coordinates": {"lat": str(lat), "lng": str(lng)},
                        "resolved_url": resolved_url
                    }
        
        return {"success": False, "error": "No valid coordinates found"}
        
    except requests.RequestException as e:
        return {"success": False, "error": f"Failed to resolve URL: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Error processing URL: {str(e)}"}

@app.post("/upload-profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Validate file size (max 5MB)
    if file.size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 5MB")
    
    # Create uploads directory if it doesn't exist
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    
    # Generate unique filename
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = uploads_dir / unique_filename
    
    try:
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Update user's photo_url in database
        current_user.photo_url = f"/uploads/{unique_filename}"
        db.commit()
        
        return {"photo_url": current_user.photo_url}
    except Exception as e:
        # Clean up file if database update fails
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail="Failed to upload profile picture")

# User management endpoints
@app.post("/users", response_model=schemas.User)
async def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Only admin can create users
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role,
        phone=user.phone,
        designation=user.designation,
        photo_url=user.photo_url
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/salespersons", response_model=List[schemas.User])
async def get_all_salespersons(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return db.query(User).filter(User.role == "salesperson").all()

@app.get("/salespersons/nearby", response_model=List[schemas.SalespersonWithDistance])
async def get_nearby_salespersons(
    lat: float,
    lng: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    salespeople = db.query(User).filter(
        User.role == "salesperson",
        User.current_latitude.isnot(None),
        User.current_longitude.isnot(None)
    ).all()
    
    sorted_salespeople = sort_salespeople_by_distance(salespeople, lat, lng)
    
    result = []
    for salesperson, distance in sorted_salespeople:
        salesperson_data = schemas.SalespersonWithDistance(
            id=salesperson.id,
            full_name=salesperson.full_name,
            phone=salesperson.phone,
            email=salesperson.email,
            designation=salesperson.designation,
            photo_url=salesperson.photo_url,
            current_latitude=salesperson.current_latitude,
            current_longitude=salesperson.current_longitude,
            last_location_update=salesperson.last_location_update,
            status=salesperson.status,
            distance_km=round(distance, 2)
        )
        result.append(salesperson_data)
    
    return result

# Location update endpoint
@app.post("/salesperson/location")
async def update_location(
    location: schemas.LocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "salesperson":
        raise HTTPException(status_code=403, detail="Only salespersons can update location")
    
    current_user.current_latitude = location.latitude
    current_user.current_longitude = location.longitude
    current_user.last_location_update = datetime.utcnow()
    
    db.commit()
    db.refresh(current_user)
    
    return {"message": "Location updated successfully"}

# Lead management endpoints
@app.post("/leads", response_model=schemas.Lead)
async def create_lead(
    lead: schemas.LeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role not in ["crm", "admin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db_lead = Lead(
        **lead.dict(),
        created_by=current_user.id
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead

@app.get("/leads", response_model=List[schemas.Lead])
async def get_leads(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return db.query(Lead).offset(skip).limit(limit).all()

# DELETE endpoint for lead deletion
@app.delete("/leads/{lead_id}")
async def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a lead - Available to CRM and Admin users"""
    if current_user.role not in ["crm", "admin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Check if lead exists
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Delete associated assignments first
    db.query(Assignment).filter(Assignment.lead_id == lead_id).delete()
    
    # Delete the lead
    db.delete(lead)
    db.commit()
    
    return {"message": f"Lead {lead_id} deleted successfully"}

# Assignment endpoints
@app.post("/assign", response_model=schemas.Assignment)
async def assign_lead_to_salesperson(
    assignment: schemas.AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role not in ["crm", "admin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Check if lead exists
    lead = db.query(Lead).filter(Lead.id == assignment.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Check if salesperson exists
    salesperson = db.query(User).filter(
        User.id == assignment.salesperson_id,
        User.role == "salesperson"
    ).first()
    if not salesperson:
        raise HTTPException(status_code=404, detail="Salesperson not found")
    
    # Create assignment
    db_assignment = Assignment(
        lead_id=assignment.lead_id,
        salesperson_id=assignment.salesperson_id,
        assigned_by=current_user.id,
        notes=assignment.notes
    )
    
    # Update lead status
    lead.status = "assigned"
    
    # Update salesperson status
    salesperson.status = "busy"
    
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    
    return db_assignment

@app.get("/assignments", response_model=List[schemas.Assignment])
async def get_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role == "salesperson":
        return db.query(Assignment).filter(Assignment.salesperson_id == current_user.id).all()
    else:
        return db.query(Assignment).all()

@app.put("/assignments/{assignment_id}", response_model=schemas.Assignment)
async def update_assignment_status(
    assignment_id: int,
    status_update: schemas.AssignmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Get the assignment
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Check permissions - salesperson can only update their own assignments
    if current_user.role == "salesperson" and assignment.salesperson_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only update your own assignments")
    elif current_user.role not in ["salesperson", "crm", "admin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Validate status values
    valid_statuses = ["pending", "accepted", "in_progress", "completed", "rejected"]
    if status_update.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    # Update assignment
    assignment.status = status_update.status
    if status_update.notes:
        assignment.notes = status_update.notes
    
    # Update completion timestamp if status is completed
    if status_update.status == "completed":
        assignment.completed_at = datetime.utcnow()
        # Update salesperson status back to available
        salesperson = db.query(User).filter(User.id == assignment.salesperson_id).first()
        if salesperson:
            salesperson.status = "available"
    elif status_update.status == "in_progress":
        # Update salesperson status to busy
        salesperson = db.query(User).filter(User.id == assignment.salesperson_id).first()
        if salesperson:
            salesperson.status = "busy"
    
    db.commit()
    db.refresh(assignment)
    return assignment

# Admin and HR user management endpoints
@app.post("/admin/users", response_model=schemas.User)
async def create_user_by_admin(
    user: schemas.UserCreateByAdmin,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role not in ["admin", "hr", "executive"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate role
    valid_roles = ["salesperson", "crm", "admin", "hr", "executive"]
    if user.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")
    
    # Only admin can create admin, hr, and executive users
    if user.role in ["admin", "hr", "executive"] and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can create admin, hr, or executive users")
    
    db_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        role=user.role,
        phone=user.phone,
        designation=user.designation,
        photo_url=user.photo_url
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.get("/admin/users", response_model=List[schemas.User])
async def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role not in ["admin", "hr", "executive"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return db.query(User).all()

@app.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete users")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}

@app.put("/admin/users/{user_id}", response_model=schemas.User)
async def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role not in ["admin", "hr", "executive"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update only provided fields
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user

# Pre-lead management endpoints
@app.post("/pre-leads", response_model=schemas.PreLead)
async def create_pre_lead(
    pre_lead: schemas.PreLeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role not in ["crm", "admin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    from database import PreLead
    db_pre_lead = PreLead(
        **pre_lead.dict(),
        created_by=current_user.id
    )
    db.add(db_pre_lead)
    db.commit()
    db.refresh(db_pre_lead)
    return db_pre_lead

@app.get("/pre-leads", response_model=List[schemas.PreLead])
async def get_pre_leads(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    from database import PreLead
    return db.query(PreLead).offset(skip).limit(limit).all()

@app.post("/pre-leads/{pre_lead_id}/convert", response_model=schemas.Lead)
async def convert_pre_lead_to_lead(
    pre_lead_id: int,
    convert_data: schemas.PreLeadToLeadConvert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role not in ["crm", "admin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    from database import PreLead
    # Get the pre-lead
    pre_lead = db.query(PreLead).filter(PreLead.id == pre_lead_id).first()
    if not pre_lead:
        raise HTTPException(status_code=404, detail="Pre-lead not found")
    
    if pre_lead.converted_to_lead_id:
        raise HTTPException(status_code=400, detail="Pre-lead already converted")
    
    # Create the lead from pre-lead and convert data
    db_lead = Lead(
        company_name=pre_lead.company_name,
        contact_person=convert_data.contact_person,
        phone=convert_data.phone,
        email=convert_data.email,
        address=convert_data.address,
        latitude=convert_data.latitude,
        longitude=convert_data.longitude,
        priority=convert_data.priority,
        estimated_value=convert_data.estimated_value,
        notes=f"Converted from pre-lead. Original reason: {pre_lead.reason}. Original source: {pre_lead.source}. Original classification: {pre_lead.classification}. {convert_data.notes or ''}",
        created_by=current_user.id
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    
    # Update pre-lead to mark as converted
    pre_lead.converted_to_lead_id = db_lead.id
    pre_lead.converted_at = datetime.utcnow()
    db.commit()
    
    return db_lead

@app.get("/")
async def root():
    return {"message": "Bonhoeffer Machines CRM API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
