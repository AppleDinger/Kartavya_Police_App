from src.backend.app.database import SessionLocal, engine
from src.backend.app import models, auth
import os
import random

# 1. Reset Database
if os.path.exists("police_geofencing.db"):
    try:
        os.remove("police_geofencing.db")
        print("🗑️  Deleted old database.")
    except PermissionError:
        print("⚠️  Error: Stop the backend terminal first!")
        exit()

models.Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Photos
SUP_PHOTO = "https://cdn-icons-png.flaticon.com/512/206/206853.png"
OFFICER_PHOTO = "https://cdn-icons-png.flaticon.com/512/206/206855.png"

def create_data():
    print("Creating 20 Officers with varied statuses...")

    # --- ADMINS ---
    head = models.User(username="head", hashed_password=auth.get_password_hash("admin"), role="head_officer", profile_photo=SUP_PHOTO)
    sup_n = models.User(username="sup_north", hashed_password=auth.get_password_hash("sup1"), role="supervisor", profile_photo=SUP_PHOTO)
    sup_s = models.User(username="sup_south", hashed_password=auth.get_password_hash("sup2"), role="supervisor", profile_photo=SUP_PHOTO)
    db.add_all([head, sup_n, sup_s])
    db.commit()

    # --- HELPER TO CREATE OFFICERS ---
    def create_officer(name, sup_id, status_type, lat, long):
        # status_type: safe, risk, free, on_leave, req_leave
        
        user = models.User(
            username=name,
            hashed_password=auth.get_password_hash("123"),
            role="field_officer",
            supervisor_id=sup_id,
            last_known_lat=lat,
            last_known_long=long,
            profile_photo=OFFICER_PHOTO # Add photo
        )
        
        if status_type == "on_leave":
            user.is_on_leave = True
        elif status_type == "req_leave":
            user.leave_requested = True
            
        db.add(user)
        db.commit()
        
        # Add Deployment if needed
        if status_type in ["safe", "risk"]:
            # Deployed at the given location
            target_lat = lat
            target_long = long
            # If Risk, move current location AWAY from target
            curr_lat = lat if status_type == "safe" else lat + 0.02 # ~2km away
            dep = models.Deployment(
                officer_id=user.id, target_lat=target_lat, target_long=target_long, radius_meters=500.0,
                current_lat=curr_lat, current_long=long,
                status="deployed" if status_type == "safe" else "out_of_bounds", is_active=True
            )
            db.add(dep)
            db.commit()

    # --- NORTH TEAM (10 Officers - Panaji Region) ---
    print("Generating North Team...")
    create_officer("Amit_Verma", sup_n.id, "safe", 15.4909, 73.8278)
    create_officer("Priya_Singh", sup_n.id, "safe", 15.4950, 73.8200)
    create_officer("Rahul_Naik", sup_n.id, "safe", 15.5000, 73.8300)
    create_officer("Vikram_Rao", sup_n.id, "risk", 15.5500, 73.7500)
    create_officer("Sneha_Patel", sup_n.id, "risk", 15.4800, 73.8000)
    create_officer("Arjun_Reddy", sup_n.id, "free", 15.5100, 73.8500)
    create_officer("Karan_Johar", sup_n.id, "free", 15.5200, 73.8600)
    create_officer("Rohit_Sharma", sup_n.id, "req_leave", 15.4900, 73.8200)
    create_officer("Virat_Kohli", sup_n.id, "req_leave", 15.4900, 73.8200)
    create_officer("MS_Dhoni", sup_n.id, "on_leave", 15.0000, 73.0000)

    # --- SOUTH TEAM (10 Officers - Margao Region) ---
    print("Generating South Team...")
    create_officer("Suresh_Raina", sup_s.id, "safe", 15.2736, 73.9581)
    create_officer("Hardik_Pandya", sup_s.id, "safe", 15.2800, 73.9600)
    create_officer("Jadeja_R", sup_s.id, "safe", 15.2700, 73.9500)
    create_officer("Bumrah_J", sup_s.id, "risk", 15.3000, 74.0000)
    create_officer("Shami_M", sup_s.id, "risk", 15.3100, 74.0100)
    create_officer("Ashwin_R", sup_s.id, "free", 15.2600, 73.9400)
    create_officer("Pant_R", sup_s.id, "free", 15.2500, 73.9300)
    create_officer("Gill_S", sup_s.id, "req_leave", 15.2700, 73.9500)
    create_officer("Iyer_S", sup_s.id, "on_leave", 15.0000, 73.0000)
    create_officer("Kl_Rahul", sup_s.id, "on_leave", 15.0000, 73.0000)

    print("✅ Data Created with Profile Photos!")

if __name__ == "__main__":
    create_data()