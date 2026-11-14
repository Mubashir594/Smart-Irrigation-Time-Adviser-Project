# AURA — Smart Irrigation Time Adviser
### Final-Year BCA Academic Project | Python FastAPI, SQLite & Agronomic Advisory Engine

AURA (Smart Irrigation Time Adviser) is an academic web application developed for a Bachelor of Computer Applications (BCA) final-year project. It provides a local decision-support system that estimates soil moisture depletion and calculates recommended irrigation scheduling based on crop species coefficients, soil classification, weather conditions, and elapsed time since the last watering event.

The system features a **Python FastAPI** backend, a **Python Irrigation Calculation Engine** based on FAO-56 agronomic principles, a local **SQLite** database, and a **Professional Dark UI**.

---

## 1. Project Introduction

Irrigation scheduling is often done arbitrarily or through static timers, resulting in either over-watering (which leads to root hypoxia, fertilizer runoff, and water waste) or under-watering (causing moisture deficit and permanent crop wilting). 

AURA addresses this challenge by providing a centralized, locally hosted advisory interface. Given environmental inputs, AURA calculates reference evapotranspiration ($ET_o$), applies crop coefficients ($K_c$) to obtain crop evapotranspiration ($ET_c$), estimates remaining soil moisture in the active root zone, and computes the safe time window before a critical water deficit occurs.

---

## 2. Project Objectives

- **Backend Calculation**: Execute all agronomic and mathematical formulas in a Python FastAPI backend rather than relying on client-side estimation.
- **Scientifically Grounded Estimation**: Apply FAO-56 single-crop coefficient principles ($ET_c = ET_o \times K_c$) and Available Water Capacity (AWC) parameters.
- **Actionable Decision Classification**: Categorize field status into three clear states:
  - *Optimal Equilibrium* (Moisture between 45% and 85%; maintain normal schedule).
  - *Urgent: Water Deficit* (Moisture below 45%; wilting risk; immediate watering advised).
  - *Saturation Warning* (Moisture above 85%; hypoxia risk; drainage advised).
- **Persistent SQLite Telemetry**: Store every advisory calculation, including intermediate parameters ($ET_o$, $K_c$, $ET_c$, moisture %, remaining hours), in a local database.
- **Local Authentication**: Protect the terminal using `bcrypt` password hashing and JSON Web Tokens (JWT).
- **Professional Dark Agronomic UI**: Deliver an agritech interface adhering to a modern dark palette (`#0B1220`, `#111827`, `#172033`, `#1E293B`, with `#14B8A6` teal and `#38BDF8` sky accents).

---

## 3. Technology Stack

| Tier | Technology | Purpose |
|---|---|---|
| **Frontend** | HTML5, Tailwind CSS, JavaScript | Responsive dark UI, Lucide icons, GSAP transitions |
| **Backend** | Python 3.11+, FastAPI | REST API endpoints, routing, Pydantic input validation |
| **Calculation Engine** | Python (`calculations.py`) | $ET_o$ mapping, $ET_c$ formulation, moisture and deficit timeline |
| **Database** | SQLite3 via SQLAlchemy 2.0+ | Relational data persistence (`database/aura.db`) |
| **Security** | `bcrypt`, `pyjwt` | Salted password hashing and JWT access token verification |
| **Testing** | `pytest`, `pytest-asyncio`, `httpx` | Unit and integration test suites |
| **Execution** | Local computer (Windows) | Standalone local deployment without cloud dependency |

---

## 4. Project Folder Structure

```text
AURA Project/
│
├── frontend/
│   ├── index.html              # Professional dark terminal authentication page
│   └── dash.html               # Main AURA Smart Irrigation Dashboard
│
├── backend/
│   ├── main.py                 # FastAPI app, static routing, lifespan DB hook
│   ├── database.py             # SQLite connection, engine, and SessionLocal
│   ├── models.py               # SQLAlchemy ORM models (User, IrrigationHistory, UserSettings)
│   ├── schemas.py              # Pydantic schemas for request validation & responses
│   ├── calculations.py         # Authoritative Python Irrigation Calculation Engine
│   ├── auth.py                 # Password hashing (bcrypt) and JWT handler
│   ├── init_db.py              # CLI utility to initialize DB and admin user
│   ├── requirements.txt        # Python dependencies
│   ├── test_api.py             # Backend API & database test suite
│   ├── test_server_startup.py  # Live Uvicorn startup probe test
│   │
│   └── routes/
│       ├── __init__.py
│       ├── authentication.py   # /api/auth routes (login, logout, me)
│       ├── irrigation.py       # /api/irrigation routes (calculate, history, clear)
│       └── users.py            # /api/users routes (settings get/update)
│
├── database/
│   └── aura.db                 # Local SQLite database file
│
├── tests/
│   ├── __init__.py
│   ├── test_auth.py            # Pytest suite for password hashing & JWT auth
│   ├── test_calculations.py    # Pytest suite for Python calculation engine & edge cases
│   └── test_irrigation.py      # Pytest suite for calculation API & multi-user isolation
│
├── index.html                  # Root entrypoint alias
├── dash.html                   # Root dashboard alias
├── requirements.txt            # Python dependencies (root-level alias)
├── pytest.ini                  # Pytest configuration
├── README.md                   # Complete academic documentation
└── .gitignore                  # Git exclusions
```

---

## 5. Python Irrigation Calculation Engine (`calculations.py`)

All calculations are executed in Python on the FastAPI backend.

### Agronomic Methodology & Formulas

1. **Reference Evapotranspiration ($ET_o$)**:
   Representative daily reference evapotranspiration values (in mm/day) based on FAO-56 climate approximations:
   - *Extreme Arid (Hot)*: $9.2 \text{ mm/day}$
   - *Sunny/Warm*: $6.8 \text{ mm/day}$
   - *Mild/Clear (Normal)*: $4.8 \text{ mm/day}$
   - *Cool/Overcast*: $2.8 \text{ mm/day}$
   - *Heavy Rain*: $1.2 \text{ mm/day}$
   - *Tropical/Humid*: $3.5 \text{ mm/day}$

2. **Crop Evapotranspiration ($ET_c$)**:
   Calculated using the FAO single-crop coefficient approach:
   $$ET_c = ET_o \times K_c \quad (\text{mm/day})$$
   Supported mid-season crop coefficients ($K_c$):
   - *Cereals*: Rice ($1.20$), Maize ($1.15$), Wheat ($1.10$), Barley ($1.00$)
   - *Vegetables*: Tomato ($1.15$), Potato ($1.10$), Onion ($1.05$), Carrot ($1.00$)
   - *Fruits & Specialty*: Grapes ($0.85$), Citrus ($0.75$), Coffee ($0.95$), Banana ($1.20$)

3. **Available Water Capacity (AWC in mm)**:
   Estimated Available Water Capacity (AWC) in the active root zone (the volume of water available to crops between field capacity and permanent wilting point). Note that these figures serve as approximate application parameters rather than experimentally measured soil properties:
   - *Heavy Clay*: $39.0 \text{ mm}$
   - *Silty Clay*: $33.0 \text{ mm}$
   - *Silt Loam (Loamy)*: $26.0 \text{ mm}$
   - *Sandy Loam*: $19.0 \text{ mm}$
   - *Coarse Sand*: $13.0 \text{ mm}$
   - *Peat / Organic*: $52.0 \text{ mm}$

4. **Soil Moisture Estimation**:
   $$\text{Loss (mm)} = \text{hours} \times \frac{ET_c}{24}$$
   $$\text{Depletion (\%)} = \left(\frac{\text{Loss}}{\text{AWC}}\right) \times 100$$
   $$\text{Base Moisture (\%)} = 100 - \text{Depletion}$$
   - Precipitation adjustment: $+35\%$ for `rainy`, $+8\%$ for `humid`.
   - Clamping: Strictly bounded between $5.0\%$ (residual wilting threshold) and $100.0\%$ (field capacity).

5. **Time Before Critical Deficit**:
   Managed Allowed Depletion ($MAD$) is defined at $35\%$ of Available Water Capacity (AWC).
   $$\text{Critical Water (mm)} = 0.35 \times \text{AWC}$$
   $$\text{Current Water (mm)} = \left(\frac{\text{Moisture}}{100}\right) \times \text{AWC}$$
   $$\text{Hours Remaining} = \max\left(0.0, \frac{\text{Current Water} - \text{Critical Water}}{ET_c / 24}\right)$$

---

## 6. Database Design (SQLite)

### Table 1: `users`
- `id` (INTEGER, Primary Key): Unique identifier.
- `full_name` (VARCHAR(100)): Operator full name.
- `username` (VARCHAR(50), Unique, Indexed): Unique login ID.
- `password_hash` (VARCHAR(255)): Bcrypt salted hash.
- `created_at` (DATETIME): Timestamp.

### Table 2: `irrigation_history`
- `id` (INTEGER, Primary Key): Unique calculation ID.
- `user_id` (INTEGER, Foreign Key -> `users.id`): Associated user.
- `crop_type` (VARCHAR(50)): Crop species.
- `soil_type` (VARCHAR(50)): Soil texture.
- `weather_condition` (VARCHAR(50)): Weather preset.
- `hours_since_irrigation` (INTEGER): Elapsed time.
- `eto_estimate` (FLOAT): Reference $ET_o$ in mm/day.
- `crop_coefficient` (FLOAT): $K_c$ factor.
- `etc_loss_rate` (FLOAT): $ET_c$ in mm/day.
- `estimated_moisture` (FLOAT): Soil moisture percentage.
- `estimated_time_to_critical_deficit` (FLOAT): Deficit window in hours.
- `irrigation_status` (VARCHAR(100)): Status summary.
- `recommendation` (VARCHAR(255)): Advisory directive.
- `created_at` (DATETIME): Record creation timestamp.

### Table 3: `user_settings`
- `id` (INTEGER, Primary Key): Settings ID.
- `user_id` (INTEGER, Foreign Key -> `users.id`, Unique): Associated user.
- `sensor_frequency` (VARCHAR(50)): Polling frequency preset.
- `autonomous_mode` (BOOLEAN): Simulation mode flag.
- `updated_at` (DATETIME): Last update timestamp.

---

## 7. Main API Endpoints

Interactive Swagger documentation is available at `http://127.0.0.1:8000/docs`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register new user account (Full Name, Username, Password) |
| `POST` | `/api/auth/login` | Authenticate user/admin, returns JWT access token |
| `POST` | `/api/auth/logout` | Invalidate session |
| `GET` | `/api/auth/me` | Current authenticated user profile |
| `POST` | `/api/irrigation/calculate` | Execute Python calculation engine & save record |
| `GET` | `/api/irrigation/history` | Retrieve user's calculation history (descending) |
| `GET` | `/api/irrigation/history/{id}` | Retrieve single calculation record |
| `DELETE` | `/api/irrigation/history` | Clear calculation history |
| `GET` | `/api/users/settings` | Retrieve node configuration settings |
| `PUT` | `/api/users/settings` | Update node configuration settings |
| `GET` | `/` and `/index.html` | Serves Aura OS login page |
| `GET` | `/dash.html` | Serves AURA Dashboard page |

---

## 8. Installation & Setup Instructions

### Prerequisites
- **Python 3.10, 3.11, or 3.12** installed on your computer. *(Ensure "Add Python to PATH" is checked during installation).*
- **PowerShell** or **Command Prompt (CMD)** on Windows.
- Any modern web browser (Google Chrome, Microsoft Edge, Firefox, Brave).

### Step 1: Extract ZIP & Open Terminal
Extract the `AURA Project.zip` archive to any directory on your computer (e.g. `C:\Users\<YourUsername>\Desktop` or `Downloads`). Open PowerShell or Command Prompt, and navigate into the extracted project folder:

```powershell
cd "path\to\AURA Project"
```

### Step 2: Create a Python Virtual Environment
Create a clean, isolated virtual environment inside the project directory:

```powershell
python -m venv .venv
```

### Step 3: Activate the Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell restricts script execution, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`, or activate via Command Prompt using `.\.venv\Scripts\activate.bat`)*.

### Step 4: Install Project Dependencies
Install all required packages from `requirements.txt`:

```powershell
pip install -r requirements.txt
```

---

## 9. Application Execution & Login

### Step 1: Start the FastAPI Backend Server
Run Uvicorn from the project root directory:

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

*(Alternatively, you can navigate into `backend` and run: `cd backend` then `python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000`)*.

### Step 2: Access the Application in Your Browser
Once the server starts (`Uvicorn running on http://127.0.0.1:8000`), open your browser:
- **Terminal Login Page**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Irrigation Dashboard**: [http://127.0.0.1:8000/dash.html](http://127.0.0.1:8000/dash.html)
- **Interactive API Documentation (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Step 3: Log In Using Existing Credentials
The included SQLite database (`database/aura.db`) is already pre-configured with active operator accounts. You do **not** need to reset or recreate the database:

- **Primary Administrator Account**:
  - **Auth ID / Username**: `aura_admin_01`
  - **Password**: `admin123`
- **Secondary Operator Account**:
  - **Username**: `admin123`
  - **Password**: `12345678`
  - *(Full Name: mubashir)*
- **New Account Registration**:
  - You can also register a brand new account anytime directly on the login screen by clicking the **"Register"** tab.

### Optional: Reset or Create a Custom Admin Account
If you ever wish to create an additional administrator interactively:
```powershell
python backend\init_db.py -u my_new_admin -p my_secure_password
```

### To Stop the Server
Press `Ctrl + C` in the running terminal.

---

## 10. Automated Testing

To run the complete automated test suite across calculations, authentication, and database operations:

```powershell
pytest -v tests
```

To run the end-to-end API and database integration test:
```powershell
python -u backend\test_api.py
```

To run the live server startup probe:
```powershell
python -u backend\test_server_startup.py
```

---

## 11. Known Academic Limitations (BCA Viva Reference)

1. **Predefined Meteorological Presets**: $ET_o$ values are derived from standardized representative climate conditions rather than live weather sensors (solar radiation, wind speed, vapor pressure deficit).
2. **Hardware Node Simulation**: The "Node Configuration" dialogue and API key field are simulated demonstrations. No physical IoT hardware (e.g., ESP32, Arduino) or solenoid valves are physically connected.
3. **Agronomic Model Scope**: The calculation engine uses the single-crop coefficient approach for mid-season growth. It does not model multi-stage vegetative progression or salinity stress.
4. **Local Standalone Execution**: Designed for local academic demonstrations using SQLite, not multi-node cloud clusters.
5. **Frontend CDN Resources**: Tailwind CSS, Lucide icons, and GSAP are loaded from CDNs, requiring an active internet connection when loading the web page in the browser.
