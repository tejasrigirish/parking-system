# Park Wave - 4 Wheeler Smart Parking System
**DBMS + Python Implementation • Bangalore**

A complete, robust **Smart Parking System** designed for 4-wheeler parking lots. Built using **Python 3** and **SQLite DBMS** (using Python's built-in `sqlite3` engine for zero-dependency reliability and file persistence).

---

## 🌟 Key Features

1. **Relational Database Design**:
   - `parking_slots`: Manages slot numbers (`S-01` to `S-20`), occupancy status (`Occupied`/`Vacant`), and current vehicle plate.
   - `vehicle_entries`: Stores sequential tickets, vehicle plate numbers, assigned slots, entry timestamps, exit timestamps, and billed fees.
2. **Duplicate Detection**:
   - Checks if an entering vehicle is already parked in the facility before allocating any slot.
   - Triggers the exact specified error: `"Invalid entry, the vehicle already exists"`.
3. **Automated Slot Allocation**:
   - Automatically searches and assigns the next vacant slot in order (`S-01`, `S-02`, etc.).
   - Prevents race conditions with atomic transactional updates.
4. **Interactive 2D Visual Slot Map**:
   - Modern visual grid showing all bays.
   - **Green** badge for Vacant bays.
   - **Red** badge for Occupied bays with vehicle registration numbers.
   - Click any bay to quick-exit or inspect.
5. **Accurate Real-Time Pricing Calculation**:
   - Flat base fare: **₹50** (strictly covers the **first 1 hour only**).
   - Additional rate: **₹20 for each additional started hour** after the 1st hour (`ceil(duration - 1)`).
   - ₹20 is **never added** before the first full hour has elapsed.
6. **Standardized Receipt Generation**:
   - Generates exact formatted receipts as specified for **Park Wave - Bangalore** with one-click `.txt` file export.
7. **Dual UI Modes**:
   - Modern **Tkinter Desktop GUI** (`app_gui.py`).
   - Interactive **Menu-Driven Console CLI** (`main_cli.py`).
8. **Zero External Dependencies**:
   - Built exclusively using Python standard libraries (`sqlite3`, `tkinter`, `datetime`, `math`, `unittest`). Runs out-of-the-box on any machine without needing `pip install`!

---

## 🏗️ System Architecture

```
trisshh/
├── database.py             # SQLite connection, DDL table creation, transactional CRUD
├── parking_manager.py      # Business logic: duplicate check, allocation, pricing, receipts
├── app_gui.py              # Modern Tkinter desktop GUI with visual bay grid
├── main_cli.py             # Interactive menu-driven console CLI
├── seed_data.py            # Sample data generator (active vehicles + past history)
├── test_parking_system.py  # Comprehensive automated unit test suite (8/8 passed)
├── schema.sql              # Raw SQL DDL schema definitions
├── ER_DIAGRAM.md           # ER Diagram (Mermaid) and table specifications
├── run.bat                 # One-click Windows batch file to launch Desktop GUI
├── run_cli.bat             # One-click Windows batch file to launch Console CLI
└── README.md               # Complete documentation and project report
```

---

## 🗄️ Database Schema Design

### 1. `parking_slots` Table
```sql
CREATE TABLE IF NOT EXISTS parking_slots (
    slot_no TEXT PRIMARY KEY,
    status TEXT NOT NULL CHECK(status IN ('Occupied', 'Vacant')),
    vehicle_no TEXT DEFAULT NULL
);
```

### 2. `vehicle_entries` Table
```sql
CREATE TABLE IF NOT EXISTS vehicle_entries (
    ticket_no INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_no TEXT NOT NULL,
    slot_no TEXT NOT NULL,
    entry_time TEXT NOT NULL,
    exit_time TEXT DEFAULT NULL,
    amount REAL DEFAULT NULL,
    FOREIGN KEY (slot_no) REFERENCES parking_slots(slot_no)
);
```

---

## 🔍 Duplicate Entry Prevention Logic

When a vehicle attempts entry, the system verifies whether that vehicle is already marked as actively parked:

```python
active_entry = self.db.get_active_entry_by_vehicle(clean_vehicle)
if active_entry:
    return False, "Invalid entry, the vehicle already exists", None
```

- Query executed:
  ```sql
  SELECT ticket_no, vehicle_no, slot_no, entry_time 
  FROM vehicle_entries 
  WHERE UPPER(vehicle_no) = ? AND exit_time IS NULL;
  ```
- If a record is returned, the system rejects the entry, halts slot allocation, and informs the operator:
  > **"Invalid entry, the vehicle already exists"**

---

## 💰 Pricing Formula & Real-Time Tariff Calculation

The parking fee is calculated strictly according to actual elapsed parking time:

$$\text{Duration} = \text{Current Time} - \text{Entry Time}$$

### Tariff Rules:
- **Base Fare**: **₹50** strictly covers the **first 1 hour only**.
- **Additional Hourly Charge**: If duration $> 1\text{ hour}$, add **₹20 for each additional started hour**:
  $$\text{Additional Hours} = \left\lceil \text{Duration in Hours} - 1 \right\rceil$$
  $$\text{Total Fee} = \text{₹50} + (\text{Additional Hours} \times \text{₹20})$$
- **Important**: **₹20 is NEVER added before the first complete hour has elapsed.**

### Calculation Examples:
| Actual Parked Duration | Billed Breakdown | Base Fee | Addl Fee (₹20/hr) | Total Amount Due |
| :--- | :--- | :--- | :--- | :--- |
| **0 minutes** | Base Fare | ₹50 | ₹0 | **₹50.00** |
| **30 minutes** | Base Fare | ₹50 | ₹0 | **₹50.00** |
| **59 minutes** | Base Fare | ₹50 | ₹0 | **₹50.00** |
| **1 hour 00 minutes** | 1 hour (exact) | ₹50 | ₹0 | **₹50.00** |
| **1 hour 01 minute** | 1 hr base + 1 addl hr | ₹50 | ₹20 × 1 = ₹20 | **₹70.00** |
| **1 hour 30 minutes** | 1 hr base + 1 addl hr | ₹50 | ₹20 × 1 = ₹20 | **₹70.00** |
| **1 hour 59 minutes** | 1 hr base + 1 addl hr | ₹50 | ₹20 × 1 = ₹20 | **₹70.00** |
| **2 hours 00 minutes** | 1 hr base + 1 addl hr | ₹50 | ₹20 × 1 = ₹20 | **₹70.00** |
| **2 hours 01 minute** | 1 hr base + 2 addl hrs | ₹50 | ₹20 × 2 = ₹40 | **₹90.00** |
| **3 hours 00 minutes** | 1 hr base + 2 addl hrs | ₹50 | ₹20 × 2 = ₹40 | **₹90.00** |
| **3 hours 01 minute** | 1 hr base + 3 addl hrs | ₹50 | ₹20 × 3 = ₹60 | **₹110.00** |

---

## 🧾 Receipt Formats

### 1. Entry Pass / Receipt
Issued immediately when vehicle is allotted a bay:
```
        Park Wave - 4 Wheeler Parking
                Bangalore
----------------------------------------
Ticket No   : 12
Vehicle No  : KA 01 AB 1234
Entry Time  : 2026-09-02 21:45:00
Slot No     : S-06
----------------------------------------
Amount to Pay: ₹50.00 (Base Fee)
----------------------------------------
      Thank you, visit again!
```

### 2. Exit Bill / Receipt
Issued upon vehicle exit and fee payment:
```
Park Wave - 4 Wheeler Parking, Bangalore
----------------------------------------
Ticket No        : 12
Vehicle No       : KA 01 AB 1234
Slot             : S-06
Entry Time       : 2026-09-02 18:45:00
Exit Time        : 2026-09-02 21:45:00
Total Duration   : 3h 0m
----------------------------------------
Total Amount Paid: ₹90.00
----------------------------------------
        Thank you, visit again!
```

---

## 🚀 How to Run in a Separate Window

### Option 1: Native Desktop Application (Zero Terminal / Pure Window)
- **Double-click [`ParkWave_App.pyw`](file:///c:/Users/HP/Desktop/trisshh/ParkWave_App.pyw)**:
  Runs directly with `pythonw.exe`. Opens exclusively in a modern, standalone desktop graphical window with **no terminal or command prompt window**.
- **Double-click [`run.bat`](file:///c:/Users/HP/Desktop/trisshh/run.bat)**:
  Immediately launches the separate GUI window and closes the launcher.
- **Run via Python**:
  ```powershell
  & "C:\Users\HP\AppData\Local\Programs\Python\Python312\python.exe" main.py
  # or
  python main.py
  ```

### Option 2: Run CLI in a Separate Window
- **Double-click [`run_cli.bat`](file:///c:/Users/HP/Desktop/trisshh/run_cli.bat)**:
  Spawns an independent, standalone Command Prompt window instead of running inside the IDE terminal.
- From inside `main_cli.py`, you can also select **Option [7]** to immediately launch the separate GUI window!

---

## 🧪 Test Suite Results

The system includes a dedicated unit test suite in `test_parking_system.py`:
- `test_01_initial_slots`: Verifies slot generation and default vacant states.
- `test_02_successful_vehicle_entry`: Verifies slot allotment and database persistence.
- `test_03_duplicate_entry_check`: Verifies that duplicate entry attempts trigger `"Invalid entry, the vehicle already exists"`.
- `test_04_parking_full`: Verifies rejection when all bays are occupied.
- `test_05_pricing_logic`: Validates fee calculations for partial hours, exact hours, and multi-hour stays.
- `test_06_vehicle_exit_and_slot_release`: Validates fee recording, slot release back to `Vacant`, and re-entry capability.
- `test_07_search_functionality`: Validates search by vehicle plate.
- `test_08_receipt_format`: Validates all required receipt fields and structure.

**Test Run Output**:
```
Ran 8 tests in 3.018s
OK
```
