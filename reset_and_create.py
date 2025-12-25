import random
from sqlalchemy import text
from src.backend.app.database import SessionLocal, engine
from src.backend.app import models, auth

# --- CONFIGURATION ---
SUP_PHOTO = "https://cdn-icons-png.flaticon.com/512/206/206853.png"
OFFICER_PHOTO = "https://cdn-icons-png.flaticon.com/512/727/727399.png"

FIRST_NAMES = ["Amit", "Suresh", "Rohan", "Priya", "Anjali", "Vikram", "Rahul", "Sneha", "Deepak", "Pooja", "Arjun", "Kavita", "Manish", "Rajesh", "Meera", "Nikhil", "Sanjay", "Varun", "Simran", "Neha"]
LAST_NAMES = ["Sharma", "Verma", "Patel", "Singh", "Naik", "Desai", "Gawde", "Fernandes", "Pereira", "Rodrigues", "Gupta", "Mishra", "Reddy", "Kumar", "Yadav"]

def get_random_name():
    return f"{random.choice(FIRST_NAMES)}_{random.choice(LAST_NAMES)}"

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
    """Force delete all tables to fix conflicts."""
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

    # 2. Create Field Officers
    print("🚓 Generating 20 Random Field Units...")
    
    used_names = set()
    officers = []

    for i in range(20):
        # Determine Region (First 10 North, Next 10 South)
        is_north = i < 10
        supervisor = sup_n if is_north else sup_s
        region_str = "north" if is_north else "south"

        # Unique Name Generation
        name = get_random_name()
        while name in used_names:
            name = get_random_name()
        used_names.add(name)

        # Random Location
        lat, long = get_random_coords(region_str)
        
        # Varied Status (Randomly assign some to Leave or Risk)
        status_roll = random.random()
        on_leave = False
        leave_req = False
        
        if status_roll > 0.90:
            on_leave = True # 10% chance
        elif status_roll > 0.80:
            leave_req = True # 10% chance

        # Special Case: Keep one known user for testing
        if i == 0:
            name = "Amit_Verma"
            password = "123"
        else:
            password = "pass"

        off = models.User(
            username=name,
            hashed_password=auth.get_password_hash(password),
            role="field_officer",
            supervisor_id=supervisor.id,
            last_known_lat=lat if not on_leave else None,
            last_known_long=long if not on_leave else None,
            is_on_leave=on_leave,
            leave_requested=leave_req,
            profile_photo=OFFICER_PHOTO
        )
        officers.append(off)
        print(f"   -> Created {name} ({'North' if is_north else 'South'})")

    db.add_all(officers)
    db.commit()
    print("✅ SUCCESS: 20 Unique Officers created across Goa!")
    db.close()

if __name__ == "__main__":
    create_data()