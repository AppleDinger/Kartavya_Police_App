from sqlalchemy import text
from src.backend.app.database import SessionLocal, engine
from src.backend.app import models, auth

# --- CONFIGURATION ---
SUP_PHOTO = "https://cdn-icons-png.flaticon.com/512/206/206853.png"
OFFICER_PHOTO = "https://cdn-icons-png.flaticon.com/512/727/727399.png"

def reset_database():
    """Force delete all tables to fix the UniqueViolation error."""
    print("🔥 Force deleting all tables...")
    with engine.connect() as conn:
        # Using CASCADE to remove dependent tables automatically
        conn.execute(text("DROP TABLE IF EXISTS notification_logs CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pings CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS deployments CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        conn.commit()
    print("✅ Database wiped clean.")

def create_data():
    # 1. Wipe DB
    reset_database()
    
    # 2. Re-create Tables
    print("🏗️  Creating new tables...")
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()

    # 3. Create Key Personnel
    print("👮 Creating Supervisors...")
    head = models.User(username="head", hashed_password=auth.get_password_hash("admin"), role="head_officer", profile_photo=SUP_PHOTO)
    sup_n = models.User(username="sup_north", hashed_password=auth.get_password_hash("sup1"), role="supervisor", profile_photo=SUP_PHOTO)
    sup_s = models.User(username="sup_south", hashed_password=auth.get_password_hash("sup2"), role="supervisor", profile_photo=SUP_PHOTO)
    
    db.add_all([head, sup_n, sup_s])
    db.commit()

    # 4. Create Officers
    print("🚓 Creating 20 Field Units...")
    officers = []
    # North Goa Officers (10)
    for i in range(1, 11):
        username = f"Amit_Verma" if i == 1 else f"North_Unit_{i}"
        password = "123" if i == 1 else "pass"
        off = models.User(
            username=username,
            hashed_password=auth.get_password_hash(password),
            role="field_officer",
            supervisor_id=sup_n.id,
            last_known_lat=15.60 + (i * 0.01), # Spread them out
            last_known_long=73.85 + (i * 0.01),
            profile_photo=OFFICER_PHOTO
        )
        officers.append(off)

    # South Goa Officers (10)
    for i in range(1, 11):
        off = models.User(
            username=f"South_Unit_{i}",
            hashed_password=auth.get_password_hash("pass"),
            role="field_officer",
            supervisor_id=sup_s.id,
            last_known_lat=15.20 + (i * 0.01),
            last_known_long=74.00 + (i * 0.01),
            profile_photo=OFFICER_PHOTO
        )
        officers.append(off)

    db.add_all(officers)
    db.commit()
    print("✅ SUCCESS: Data Created! You can now login.")
    db.close()

if __name__ == "__main__":
    create_data()