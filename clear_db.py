"""Quick script to clear all parking data and reset all slots to Vacant."""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parking_system.db")
with sqlite3.connect(db_path) as conn:
    conn.execute("DELETE FROM vehicle_entries;")
    conn.execute("DELETE FROM parking_slots;")
    conn.execute("DELETE FROM sqlite_sequence WHERE name='vehicle_entries';")
    slots = [(f"S-{i:02d}", "Vacant", None) for i in range(1, 21)]
    conn.executemany("INSERT OR REPLACE INTO parking_slots VALUES (?, ?, ?);", slots)
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM parking_slots").fetchone()[0]
    occupied = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE status='Occupied'").fetchone()[0]
    entries = conn.execute("SELECT COUNT(*) FROM vehicle_entries").fetchone()[0]
    print(f"Slots: {count}, Occupied: {occupied}, Entries: {entries}")
    print("Database cleared successfully - all 20 bays reset to Vacant.")
