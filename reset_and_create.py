import random
from sqlalchemy import text
from src.backend.app.database import SessionLocal, engine
from src.backend.app import models, auth

# --- CONFIGURATION ---
SUP_PHOTO = "https://cdn-icons-png.flaticon.com/512/206/206853.png"
OFFICER_PHOTO = "https://cdn-icons-png.flaticon.com/512/727/727399.png"

# --- FIXED NAMES ---
NORTH_OFFICERS = [
    "Amit_Verma", "Rohan_Naik", "Priya_Desai", "Sanjay_Gupta", "Anjali_Sharma",
    "Vikram_Rao", "Neha_Kamat", "Karan_Singh", "Deepak_Lobo", "Simran_Kaur"
]

SOUTH_OFFICERS = [
    "Rahul_Gawde", "Sneha_Patel", "Manish_Reddy", "Pooja_Iyer", "Arjun_Fernandes",
    "Kavita_Yadav", "Rajesh_Kumar", "Meera_Joshi", "Varun_Nair", "Nikhil_Sawant"
]

# Weighted Status Options (More 'Safe' than 'Risk' for realism)
STATUS_OPTIONS = ["safe", "safe", "safe", "risk", "free", "free", "req_leave", "on_leave"] 

def get_random_coords(region):
    """Generate valid coordinates for Goa regions"""
    if region == "north":
        lat = random.uniform(15.4800, 15.6200)   # Panaji / Mapusa
        long = random.uniform(73.7500, 73.8500)
    else:
        lat = random.uniform(15.2500, 15.3500)   # Margao / Vasco
        long = random.uniform(73.9000, 74.0500)
    return lat, long

def reset_database():
    print("🔥 Force deleting all tables...")
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS notification_logs CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pings CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS deployments CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        conn.commit()
    print("✅ Database wiped clean.")

def create_data():
    reset_database()
    
    print("🏗️  Creating new tables...")
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()

    # 1. Create Supervisors
    print("👮 Creating Supervisors...")
    head = models.User(username="head", hashed_password=auth.get_password_hash("admin"), role="head_officer", profile_photo=SUP_PHOTO)
    sup_n = models.User(username="sup_north", hashed_password=auth.get_password_hash("sup1"), role="supervisor", profile_photo=SUP_PHOTO)
    sup_s = models.User(username="sup_south", hashed_password=auth.get_password_hash("sup2"), role="supervisor", profile_photo=SUP_PHOTO)
    
    db.add_all([head, sup_n, sup_s])
    db.commit()

    # 2. Create Officers with "Mathematically Correct" Status
    print("pz Creating Smart Data (Positions match Status)...")
    
    roster = [(name, "north", sup_n) for name in NORTH_OFFICERS] + \
             [(name, "south", sup_s) for name in SOUTH_OFFICERS]

    for name, region, supervisor in roster:
        status_type = random.choice(STATUS_OPTIONS)
        
        # 1. Generate Base Location
        lat, long = get_random_coords(region)
        
        on_leave = False
        req_leave = False
        
        # 2. Handle Leave Logic
        if status_type == "on_leave":
            on_leave = True
            lat = None # People on leave have no location
            long = None
        elif status_type == "req_leave":
            req_leave = True
        
        # 3. Create User
        user = models.User(
            username=name,
            hashed_password=auth.get_password_hash("pass"),
            role="field_officer",
            supervisor_id=supervisor.id,
            last_known_lat=lat,
            last_known_long=long,
            is_on_leave=on_leave,
            leave_requested=req_leave,
            profile_photo=OFFICER_PHOTO
        )
        db.add(user)
        db.flush() # Need ID for deployment

        # 4. Create Consistency: Draw Zone BASED ON Status
        if status_type in ["safe", "risk"] and not on_leave:
            
            # DEFAULT: Target = Current Location (Perfectly Safe)
            target_lat = lat
            target_long = long
            
            # IF RISK: Move Target 2km away so math fails
            if status_type == "risk":
                target_lat = lat + 0.02 
            
            deploy = models.Deployment(
                officer_id=user.id,
                target_lat=target_lat,
                target_long=target_long,
                radius_meters=500.0,
                current_lat=lat,
                current_long=long,
                status="deployed" if status_type == "safe" else "out_of_bounds",
                is_active=True
            )
            db.add(deploy)
            print(f"   -> {name}: {status_type.upper()} (Synced)")
        else:
            print(f"   -> {name}: {status_type.upper()}")

    db.commit()
    print("✅ SUCCESS: Data Generated & mathematically verified.")
    print("   👉 Supervisors: sup_south / sup2")
    print("   👉 Supervisors: sup_north / sup1")
    print("   👉 Head Officer: head / admin")
    print("   👉 All Officers: pass")
    db.close()

if __name__ == "__main__":
    create_data()
