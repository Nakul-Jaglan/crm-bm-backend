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
from database import get_db, User, Lead, Assignment
from auth import (
    authenticate_user, create_access_token, get_current_active_user,
    get_password_hash, get_user_by_email
)
from utils import sort_salespeople_by_distance
from config import settings

app = FastAPI(title="Bonhoeffer Machines CRM API", version="1.0.0")

# Mount static files for uploaded images (create directory if it doesn't exist)
import os
uploads_dir = "uploads"
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.get("/")
async def root():
    return {"message": "Bonhoeffer Machines CRM API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Vercel handler
handler = app
