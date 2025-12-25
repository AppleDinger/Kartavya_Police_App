import random
import sys
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

STATUS_OPTIONS = ["safe", "safe", "safe", "risk", "free", "free", "req_leave", "on_leave"] 

def get_random_coords(region):
    if region == "north":
        lat = random.uniform(15.4800, 15.6200)   # Panaji / Mapusa
        long = random.uniform(73.7500, 73.8500)
    else:
        lat = random.uniform(15.2500, 15.3500)   # Margao / Vasco
        long = random.uniform(73.9000, 74.0500)
    return lat, long

def reset_database():
    """Interactive Switch Case for Reset Mode"""
    print("\n⚠️  DATABASE RESET MENU ⚠️")
    print("----------------------------")
    print("1. [TRUNCATE] Clean Data Only (Fast, NO Redeploy needed)")
    print("2. [DROP]     Destroy Everything (Hard Reset, MUST Redeploy Backend)")
    print("----------------------------")
    
    choice = input("👉 Select Option (1 or 2): ").strip()

    with engine.connect() as conn:
        if choice == "1":
            print("\n🧹 TRUNCATING tables (Keeping structure)...")
            # Truncate deletes rows but keeps the table alive. 'RESTART IDENTITY' resets IDs to 1.
            conn.execute(text("TRUNCATE TABLE notification_logs, pings, deployments, users RESTART IDENTITY CASCADE"))
            conn.commit()
            print("✅ Tables emptied.")
            return "truncate"

        elif choice == "2":
            print("\n🔥 DROPPING all tables (Nuclear Option)...")
            conn.execute(text("DROP TABLE IF EXISTS notification_logs CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS pings CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS deployments CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            conn.commit()
            print("✅ Tables destroyed.")
            return "drop"
        
        else:
            print("❌ Invalid selection. Exiting.")
            sys.exit()

def create_data():
    # 1. Ask User & Reset DB
    mode = reset_database()
    
    # 2. If DROP mode was used, we must re-create tables
    if mode == "drop":
        print("🏗️  Re-creating table structure...")
        models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()

    # 3. Create Supervisors
    print("👮 Creating Supervisors...")
    head = models.User(username="head", hashed_password=auth.get_password_hash("admin"), role="head_officer", profile_photo=SUP_PHOTO)
    sup_n = models.User(username="sup_north", hashed_password=auth.get_password_hash("sup1"), role="supervisor", profile_photo=SUP_PHOTO)
    sup_s = models.User(username="sup_south", hashed_password=auth.get_password_hash("sup2"), role="supervisor", profile_photo=SUP_PHOTO)
    
    db.add_all([head, sup_n, sup_s])
    db.commit()

    # 4. Create Officers with Smart Status Logic
    print("🚓 Creating Officers with Synced Status...")
    
    roster = [(name, "north", sup_n) for name in NORTH_OFFICERS] + \
             [(name, "south", sup_s) for name in SOUTH_OFFICERS]

    for name, region, supervisor in roster:
        status_type = random.choice(STATUS_OPTIONS)
        lat, long = get_random_coords(region)
        
        on_leave = (status_type == "on_leave")
        req_leave = (status_type == "req_leave")
        
        if on_leave:
            lat, long = None, None

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
        db.flush()

        if status_type in ["safe", "risk"] and not on_leave:
            target_lat, target_long = lat, long
            if status_type == "risk":
                target_lat = lat + 0.02 # Force mismatch

            deploy = models.Deployment(
                officer_id=user.id,
                target_lat=target_lat, target_long=target_long, radius_meters=500.0,
                current_lat=lat, current_long=long,
                status="deployed" if status_type == "safe" else "out_of_bounds",
                is_active=True
            )
            db.add(deploy)
            print(f"   -> {name}: {status_type.upper()} (Synced)")
        else:
            print(f"   -> {name}: {status_type.upper()}")

    db.commit()
    print("\n✅ SUCCESS: Data Refreshed!")
    if mode == "drop":
        print("⚠️  REMINDER: You used DROP mode. You MUST redeploy your backend on Render now!")
    else:
        print("🚀 TRUNCATE mode used. No redeploy needed. Refresh your dashboard!")

    print("🔗 Login Credentials:")
    print("   - Head Officer: username='head', password='admin'")
    print("   - Supervisors:  username='sup_north', password='sup1' | username='sup_south', password='sup2'")
    print("   - Field Officers: username='<Officer_Name>', password='pass' (e.g., 'Amit_Verma')")    
    db.close()

if __name__ == "__main__":
    create_data()