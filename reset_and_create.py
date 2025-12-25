import random
from sqlalchemy import text
from src.backend.app.database import SessionLocal, engine
from src.backend.app import models, auth

# --- CONFIGURATION ---
SUP_PHOTO = "https://cdn-icons-png.flaticon.com/512/206/206853.png"
OFFICER_PHOTO = "https://cdn-icons-png.flaticon.com/512/727/727399.png"

# --- FIXED ROSTER ---
NORTH_OFFICERS = [
    "Amit_Verma", "Rohan_Naik", "Priya_Desai", "Sanjay_Gupta", "Anjali_Sharma",
    "Vikram_Rao", "Neha_Kamat", "Karan_Singh", "Deepak_Lobo", "Simran_Kaur"
]

SOUTH_OFFICERS = [
    "Rahul_Gawde", "Sneha_Patel", "Manish_Reddy", "Pooja_Iyer", "Arjun_Fernandes",
    "Kavita_Yadav", "Rajesh_Kumar", "Meera_Joshi", "Varun_Nair", "Nikhil_Sawant"
]

def get_random_coords(region):
    """Generate valid coordinates for Goa regions"""
    if region == "north":
        # Panaji / Mapusa area
        lat = random.uniform(15.4800, 15.6200)
        long = random.uniform(73.7500, 73.8500)
    else:
        # Margao / Vasco area
        lat = random.uniform(15.2500, 15.3500)
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

    # 2. Create North Team
    print("🚓 Creating North Team (Panaji Region)...")
    for name in NORTH_OFFICERS:
        lat, long = get_random_coords("north")
        # Uniform password for everyone
        off = models.User(
            username=name,
            hashed_password=auth.get_password_hash("pass"),
            role="field_officer",
            supervisor_id=sup_n.id,
            last_known_lat=lat,
            last_known_long=long,
            profile_photo=OFFICER_PHOTO
        )
        db.add(off)

    # 3. Create South Team
    print("🚓 Creating South Team (Margao Region)...")
    for name in SOUTH_OFFICERS:
        lat, long = get_random_coords("south")
        # Uniform password for everyone
        off = models.User(
            username=name,
            hashed_password=auth.get_password_hash("pass"),
            role="field_officer",
            supervisor_id=sup_s.id,
            last_known_lat=lat,
            last_known_long=long,
            profile_photo=OFFICER_PHOTO
        )
        db.add(off)

    db.commit()
    print("   👉 Supervisors: sup_north / sup1")
    print("   👉 Supervisors: sup_south / sup2")
    print("   👉 ALL Officers: [Any Name] / pass")
    db.close()

if __name__ == "__main__":
    create_data()