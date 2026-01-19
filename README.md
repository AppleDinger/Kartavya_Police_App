# Kartvya- Police Geofencing Command Center

A tactical command dashboard for managing police field units, tracking real-time locations, and handling deployment/leave requests.
https://kartavya-police-app-frontend.onrender.com/

--------------------------------------------------------------------------------

## Quick Setup

### 1. Prerequisites
- Python 3.11 or higher
- Windows PowerShell (or Git Bash)

### 2. Installation
Open your terminal in the project folder:

```powershell
# Create virtual environment
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 3\. Database Setup

Run this script to generate the sample database with **20 Officers** (Safe, Risk, Free, On Leave) and **2 Supervisors**.

```powershell
python create_sample_data.py
```

-----

## Running the Application

You need **two separate terminals** running at the same time.

**Terminal 1: Backend API**

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn src.backend.app.main:app --reload
```

**Terminal 2: Frontend Dashboard**

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run src\frontend\app.py
```

*The app will open automatically at http://localhost:8501*

-----

## Login Credentials

### 1\. Supervisor (Command HQ)

Login here to view the tactical map, deploy units, and approve leave.

| Role | Username | Password | Jurisdiction |
|------|----------|----------|--------------|
| **Supervisor (North)** | `sup_north` | `sup1` | Panaji / North Goa |
| **Supervisor (South)** | `sup_south` | `sup2` | Margao / South Goa |
| **Head Officer** | `head` | `admin` | Global View |

### 2\. Field Officers (Mobile Units)

Login here to simulate GPS movement, view your assigned zone, and request leave.

| Status | Username | Password | Behavior on Map |
|--------|----------|----------|----------------|
| **SAFE** | `Amit_Verma` | `123` | 🟢 Inside Zone (Green) |
| **RISK** | `Vikram_Rao` | `123` | 🔴 Outside Zone (Red) |
| **FREE** | `Arjun_Reddy` | `123` | 🟡 Waiting for Deployment |
| **LEAVE** | `MS_Dhoni` | `123` | 🔵 On Leave (Blue) |

-----

## Key Features

	- **Tactical Map:** Real-time view of all units with status color coding.
	- **Bulk Deployment:** Supervisors can select multiple free units and deploy them to a specific coordinate.
	- **Unit Command:** Stop patrols, grant leave, or recall units instantly.
	- **GPS Simulation:** Field officers can manually input coordinates to test geofencing triggers.
	- **Smart Notifications:** Real-time alerts for boundary violations and leave requests.



## Licensing & Open Source Disclosure
Kartavya is licensed under the GNU AGPLv3.

Unlike the standard GPL, the Affero license specifically closes the "SaaS Loophole." If you modify this code and run it on a server to provide services to users over a network (such as a private police department cloud), you are legally obligated to make your modified source code available to those users. > This ensures that improvements to this critical public safety infrastructure remain open to the public and the personnel using it.

