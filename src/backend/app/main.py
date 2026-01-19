/*
 * Kartavya - Police Personnel Management & Geofencing Suite
 * Copyright (C) 2026 [Your Full Name]
 * * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as 
 * published by the Free Software Foundation, either version 3 of the 
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <https://www.gnu.org/licenses/>.
 */
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import math

# --- FIX: Import models correctly ---
from . import models, auth, database
from .services import geofencing_service

# Create tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Police Geofencing API")

# --- INTERNAL HELPERS ---
def calculate_distance(lat1, lon1, lat2, lon2):
    if not lat1 or not lon1 or not lat2 or not lon2: return 999999
    R = 6371000 # meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R*c

def log_event(db: Session, level: str, message: str, user_id: int = None):
    db.add(models.NotificationLog(level=level, message=message, user_id=user_id))
    db.commit()

# --- SCHEMAS ---
class UserLogin(BaseModel): username: str; password: str
class CheckInRequest(BaseModel): latitude: float; longitude: float
class BulkDeployRequest(BaseModel): officer_ids: List[int]; latitude: float; longitude: float; radius: float
class PingRequest(BaseModel): receiver_id: int; message: str
class BroadcastPingRequest(BaseModel): message: str
class PingResponse(BaseModel): id: int; sender: str; message: str; lat: float; long: float; timestamp: datetime
class LogResponse(BaseModel): timestamp: datetime; level: str; message: str

class OfficerDashboardData(BaseModel):
    status: str; message: str; target_lat: Optional[float]; target_long: Optional[float]; radius: Optional[float]
    current_lat: Optional[float]; current_long: Optional[float]; profile_photo: str; pings_enabled: bool

class OfficerStatusResponse(BaseModel):
    id: int; username: str; current_lat: Optional[float]; current_long: Optional[float]
    status_color: str; leave_requested: bool; profile_photo: str; pings_enabled: bool

# --- ENDPOINTS ---

@app.post("/auth/login")
def login(creds: UserLogin, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == creds.username).first()
    if not user or not auth.verify_password(creds.password, user.hashed_password):
        raise HTTPException(403, "Invalid credentials")
    return {"access_token": auth.create_access_token({"sub": user.username, "role": user.role}), "role": user.role, "username": user.username, "profile_photo": user.profile_photo}

@app.get("/officer/me", response_model=OfficerDashboardData)
def get_my_status(u: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    status_msg, notif = "free", "AWAITING DEPLOYMENT"
    t_lat, t_long, rad = None, None, None

    if u.is_on_leave: 
        status_msg, notif = "on_leave", "ON LEAVE STATUS ACTIVE"
    else:
        dep = db.query(models.Deployment).filter(models.Deployment.officer_id == u.id, models.Deployment.is_active == True).first()
        if dep:
            t_lat, t_long, rad = dep.target_lat, dep.target_long, dep.radius_meters
            status_msg, notif = "risk", "GPS SIGNAL LOST"
            if u.last_known_lat:
                is_safe, dist = geofencing_service.is_inside_geofence(u.last_known_lat, u.last_known_long, dep.target_lat, dep.target_long, dep.radius_meters)
                status_msg, notif = ("safe", "ZONE SECURE") if is_safe else ("risk", f"VIOLATION ({int(dist)}m)")
    
    if u.leave_requested: status_msg, notif = "req_leave", "LEAVE PENDING"

    return OfficerDashboardData(
        status=status_msg, message=notif, target_lat=t_lat, target_long=t_long, radius=rad,
        current_lat=u.last_known_lat, current_long=u.last_known_long, profile_photo=u.profile_photo, pings_enabled=u.pings_enabled
    )

@app.get("/officer/logs", response_model=List[LogResponse])
def get_officer_logs(u: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    return db.query(models.NotificationLog).filter(or_(models.NotificationLog.user_id == u.id, models.NotificationLog.user_id == None)).order_by(desc(models.NotificationLog.timestamp)).limit(10).all()

@app.get("/pings/active", response_model=List[PingResponse])
def get_pings(u: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if not u.pings_enabled: return []
    pings = db.query(models.Ping).filter(models.Ping.receiver_id == u.id, models.Ping.is_active == True).all()
    res = []
    for p in pings:
        sender = db.query(models.User).get(p.sender_id)
        res.append({"id": p.id, "sender": sender.username, "message": p.message, "lat": p.lat, "long": p.long, "timestamp": p.timestamp})
    return res

@app.post("/ping/send")
def send_ping(req: PingRequest, u: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    receiver = db.query(models.User).get(req.receiver_id)
    if not receiver.pings_enabled and u.role == "field_officer":
        raise HTTPException(400, "Officer has disabled pings.")
    
    # Check range for officers
    if u.role == "field_officer":
        if not u.last_known_lat or not receiver.last_known_lat: raise HTTPException(400, "Location unknown.")
        dist = calculate_distance(u.last_known_lat, u.last_known_long, receiver.last_known_lat, receiver.last_known_long)
        if dist > 5000: raise HTTPException(400, f"Target out of range ({int(dist)}m).")

    db.add(models.Ping(sender_id=u.id, receiver_id=receiver.id, message=req.message, lat=u.last_known_lat or 0, long=u.last_known_long or 0))
    db.commit()
    return {"msg": "Ping Sent"}

@app.post("/ping/broadcast")
def broadcast_ping(req: BroadcastPingRequest, u: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if not u.last_known_lat: raise HTTPException(400, "Location unknown.")
    officers = db.query(models.User).filter(models.User.role == "field_officer", models.User.id != u.id, models.User.pings_enabled == True).all()
    count = 0
    for off in officers:
        if off.last_known_lat:
            if calculate_distance(u.last_known_lat, u.last_known_long, off.last_known_lat, off.last_known_long) <= 5000:
                db.add(models.Ping(sender_id=u.id, receiver_id=off.id, message=req.message + " [BROADCAST]", lat=u.last_known_lat, long=u.last_known_long))
                count += 1
    db.commit()
    return {"msg": f"Pinged {count} units."}

@app.post("/ping/toggle")
def toggle_pings(u: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    u.pings_enabled = not u.pings_enabled; db.commit()
    return {"enabled": u.pings_enabled}

@app.post("/ping/dismiss/{pid}")
def dismiss_ping(pid: int, u: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    db.query(models.Ping).filter(models.Ping.id == pid).update({"is_active": False}); db.commit()
    return {"msg": "ok"}

@app.post("/checkin")
def check_in(loc: CheckInRequest, u: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    u.last_known_lat, u.last_known_long = loc.latitude, loc.longitude; db.commit()
    dep = db.query(models.Deployment).filter(models.Deployment.officer_id == u.id, models.Deployment.is_active == True).first()
    if dep:
        dep.current_lat, dep.current_long, dep.last_checkin = loc.latitude, loc.longitude, datetime.utcnow()
        safe, _ = geofencing_service.is_inside_geofence(loc.latitude, loc.longitude, dep.target_lat, dep.target_long, dep.radius_meters)
        dep.status = "deployed" if safe else "out_of_bounds"
        db.commit()
    return {"status": "ok"}

@app.get("/status/all", response_model=List[OfficerStatusResponse])
def get_all_status(u: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    q = db.query(models.User).filter(models.User.role == "field_officer")
    if u.role == "supervisor": q = q.filter(models.User.supervisor_id == u.id)
    res = []
    for o in q.all():
        color = "yellow"
        if o.is_on_leave: color = "blue"
        else:
            d = db.query(models.Deployment).filter(models.Deployment.officer_id == o.id, models.Deployment.is_active == True).first()
            if d: color = "green" if d.status == "deployed" else "red"
        res.append(OfficerStatusResponse(id=o.id, username=o.username, current_lat=o.last_known_lat, current_long=o.last_known_long, status_color=color, leave_requested=o.leave_requested, profile_photo=o.profile_photo, pings_enabled=o.pings_enabled))
    return res

@app.post("/deploy/bulk")
def bulk_deploy(req: BulkDeployRequest, u: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    db.query(models.Deployment).filter(models.Deployment.officer_id.in_(req.officer_ids), models.Deployment.is_active == True).update({"is_active": False}, synchronize_session=False)
    db.add_all([models.Deployment(officer_id=oid, target_lat=req.latitude, target_long=req.longitude, radius_meters=req.radius, status="deployed") for oid in req.officer_ids])
    for oid in req.officer_ids: log_event(db, "INFO", "New Deployment Assigned", user_id=oid)
    db.commit()
    return {"msg": "ok"}

@app.post("/leave/approve/{oid}")
def approve_leave(oid: int, u: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    off = db.query(models.User).get(oid); off.is_on_leave = True; off.leave_requested = False
    db.query(models.Deployment).filter(models.Deployment.officer_id == oid).update({"is_active": False})
    log_event(db, "SUCCESS", "Leave Request APPROVED", user_id=oid); db.commit()
    return {"msg": "ok"}

@app.post("/leave/deny/{oid}")
def deny_leave(oid: int, u: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    off = db.query(models.User).get(oid); off.leave_requested = False
    log_event(db, "ALERT", "Leave Request DENIED", user_id=oid); db.commit()
    return {"msg": "ok"}

@app.post("/deploy/stop/{oid}")
def stop_deploy(oid: int, u: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    db.query(models.Deployment).filter(models.Deployment.officer_id == oid).update({"is_active": False})
    log_event(db, "INFO", "Patrol Ended by Command", user_id=oid); db.commit()
    return {"msg": "ok"}

@app.post("/leave/grant/{oid}")
def grant_leave(oid: int, u: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    off = db.query(models.User).get(oid); off.is_on_leave = True; db.query(models.Deployment).filter(models.Deployment.officer_id == oid).update({"is_active": False})
    log_event(db, "SUCCESS", "Leave GRANTED by Command", user_id=oid); db.commit()
    return {"msg": "ok"}

@app.post("/leave/revoke/{oid}")
def revoke_leave(oid: int, u: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    db.query(models.User).filter(models.User.id == oid).update({"is_on_leave": False})
    log_event(db, "ALERT", "Leave REVOKED - Return to Duty", user_id=oid); db.commit()
    return {"msg": "ok"}

@app.get("/logs")
def get_logs(db: Session = Depends(database.get_db)):
    return db.query(models.NotificationLog).filter(models.NotificationLog.user_id == None).order_by(desc(models.NotificationLog.timestamp)).limit(20).all()
