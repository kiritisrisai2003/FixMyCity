"""
CityPulse AI - Main FastAPI Server
Handles all API endpoints for the civic complaint management system
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import os
from datetime import datetime, timedelta
import json
import random

# Import our modules
from backend.ai_engine import AIEngine
from backend.complaint_manager import ComplaintManager
from backend.priority_engine import PriorityEngine
from backend.image_validator import ImageValidator

app = FastAPI(title="CityPulse AI", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize managers
ai_engine = AIEngine()
complaint_manager = ComplaintManager()
priority_engine = PriorityEngine()
image_validator = ImageValidator()

# Mount static files
os.makedirs("uploads/images", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ✅ Added to serve frontend pages
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# Pydantic models
class LoginRequest(BaseModel):
    mobile: str
    otp: Optional[str] = None

class ComplaintSubmission(BaseModel):
    description: str
    location: str
    category: Optional[str] = "other"
    citizenMobile: str
    citizenName: str
    additionalAnswers: Optional[dict] = {}

class StatusUpdate(BaseModel):
    complaintId: str
    status: str
    remarks: Optional[str] = ""

class ReraiseRequest(BaseModel):
    complaintId: str
    reason: str

# In-memory OTP storage (for prototype)
otp_store = {}

@app.get("/")
async def root():
    """Serve the login page"""
    return FileResponse("frontend/login.html")

@app.post("/api/login")
async def login(request: LoginRequest):
    """Handle citizen login with OTP"""
    if not request.otp:
        otp = str(random.randint(1000, 9999))
        otp_store[request.mobile] = {
            "otp": otp,
            "expires": datetime.now() + timedelta(minutes=5)
        }
        return {
            "success": True,
            "message": f"OTP sent to {request.mobile}",
            "otp": otp
        }
    else:
        stored = otp_store.get(request.mobile)
        if not stored:
            raise HTTPException(status_code=400, detail="OTP not found or expired")
        
        if stored["otp"] == request.otp and datetime.now() < stored["expires"]:
            del otp_store[request.mobile]
            return {
                "success": True,
                "message": "Login successful",
                "token": f"token_{request.mobile}_{datetime.now().timestamp()}"
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid OTP")

@app.post("/api/submit-complaint")
async def submit_complaint(
    description: str = Form(...),
    location: str = Form(...),
    category: str = Form("other"),
    citizenMobile: str = Form(...),
    citizenName: str = Form(...),
    additionalAnswers: str = Form("{}"),
    image: Optional[UploadFile] = File(None)
):
    try:
        additional_data = json.loads(additionalAnswers)
        image_path = None
        image_validation = None
        
        if image:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{image.filename}"
            image_path = f"uploads/images/{filename}"
            
            with open(image_path, "wb") as f:
                content = await image.read()
                f.write(content)
            
            image_validation = await image_validator.validate_image(
                image_path, description, category
            )
        
        ai_analysis = await ai_engine.analyze_complaint(
            description=description,
            category=category,
            location=location,
            additional_data=additional_data,
            image_validation=image_validation
        )
        
        complaint = {
            "description": description,
            "location": location,
            "category": ai_analysis["category"],
            "citizenMobile": citizenMobile,
            "citizenName": citizenName,
            "additionalAnswers": additional_data,
            "imagePath": image_path,
            "imageValidation": image_validation,
            "aiAnalysis": ai_analysis,
            "status": "submitted"
        }
        
        complaint_id = complaint_manager.create_complaint(complaint)
        
        return {
            "success": True,
            "complaintId": complaint_id,
            "aiAnalysis": ai_analysis,
            "imageValidation": image_validation
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/complaints")
async def get_complaints(
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50
):
    complaints = complaint_manager.get_complaints(
        status=status,
        category=category,
        limit=limit
    )
    return {"success": True, "complaints": complaints}

@app.get("/api/recent-complaints")
async def get_recent_complaints(limit: int = 5):
    complaints = complaint_manager.get_complaints(limit=limit)
    return {"success": True, "complaints": complaints}

@app.get("/api/dashboard-analytics")
async def get_dashboard_analytics():
    all_complaints = complaint_manager.get_complaints(limit=1000)
    
    today = datetime.now().date()
    
    metrics = {
        "total": len(all_complaints),
        "today": len([c for c in all_complaints if c.get("timestamp", "").startswith(str(today))]),
        "inProgress": len([c for c in all_complaints if c["status"] == "in_progress"]),
        "resolved": len([c for c in all_complaints if c["status"] == "resolved"]),
        "high_priority": len([c for c in all_complaints if c.get("aiAnalysis", {}).get("priority") == "high"])
    }
    
    category_counts = {}
    for complaint in all_complaints:
        cat = complaint.get("category", "other")
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    clusters = priority_engine.create_clusters(all_complaints)
    trend_data = complaint_manager.get_trend_data(days=7)
    insights = priority_engine.generate_insights(all_complaints, clusters)
    
    return {
        "success": True,
        "metrics": metrics,
        "categoryDistribution": category_counts,
        "clusters": clusters,
        "trendData": trend_data,
        "insights": insights
    }

@app.post("/api/update-status")
async def update_status(request: StatusUpdate):
    success = complaint_manager.update_status(
        request.complaintId,
        request.status,
        request.remarks
    )
    
    if success:
        return {"success": True, "message": "Status updated successfully"}
    else:
        raise HTTPException(status_code=404, detail="Complaint not found")

@app.post("/api/reraise")
async def reraise_complaint(request: ReraiseRequest):
    success = complaint_manager.reraise_complaint(
        request.complaintId,
        request.reason
    )
    
    if success:
        return {"success": True, "message": "Complaint re-raised successfully"}
    else:
        raise HTTPException(status_code=400, detail="Cannot reraise complaint")

@app.get("/api/get-followup-questions")
async def get_followup_questions(category: str):
    questions = ai_engine.get_followup_questions(category)
    return {"success": True, "questions": questions}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ai_engine": "operational" if ai_engine.is_available() else "limited"
    }

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)