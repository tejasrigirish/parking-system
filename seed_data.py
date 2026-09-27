"""
Seed sample test entries for the Smart Parking System.
Populates realistic 4-wheeler vehicle records, active parked cars, and completed past exits.
"""

import sys

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from datetime import datetime, timedelta
import random
from database import Database
from parking_manager import ParkingManager

def seed_sample_data(reset: bool = True):
    db = Database()
    
    if reset:
        print("Resetting database tables...")
        with db.get_connection() as conn:
            conn.execute("DELETE FROM vehicle_entries;")
            conn.execute("DELETE FROM parking_slots;")
            conn.execute("DELETE FROM sqlite_sequence WHERE name='vehicle_entries';")
            slots = [(f"S-{i:02d}", "Vacant", None) for i in range(1, 21)]
            conn.executemany("INSERT INTO parking_slots VALUES (?, ?, ?);", slots)
            conn.commit()

    manager = ParkingManager(db=db)
    now = datetime.now()

    # 1. Historical Completed Entries (past 1-2 days)
    print("\n--- Seeding Completed Past Sessions ---")
    past_vehicles = [
        ("KA 01 MG 1234", now - timedelta(hours=28), timedelta(hours=3, minutes=15)),
        ("KA 03 AB 9988", now - timedelta(hours=24), timedelta(hours=1, minutes=45)),
        ("DL 08 CD 4321", now - timedelta(hours=18), timedelta(hours=5, minutes=10)),
        ("MH 12 EF 7766", now - timedelta(hours=12), timedelta(hours=2, minutes=0)),
        ("KA 05 MN 3344", now - timedelta(hours=8), timedelta(minutes=40)),
        ("TN 07 JK 5511", now - timedelta(hours=6), timedelta(hours=4, minutes=30)),
    ]

    for v_no, entry_dt, duration in past_vehicles:
        entry_str = entry_dt.strftime("%Y-%m-%d %H:%M:%S")
        exit_dt = entry_dt + duration
        exit_str = exit_dt.strftime("%Y-%m-%d %H:%M:%S")

        ok, msg, entry_info = manager.park_vehicle(v_no, custom_entry_time=entry_str)
        if ok:
            ok_exit, msg_exit, exit_info = manager.exit_vehicle(v_no, custom_exit_time=exit_str)
            print(f"[PAST] {v_no} | Entry: {entry_str} | Exit: {exit_str} | Paid: Rs. {exit_info['amount']:.2f}")

    # 2. Currently Active Parked Vehicles (varying entry times)
    print("\n--- Seeding Currently Active Parked Vehicles ---")
    active_vehicles = [
        ("KA 01 MJ 5544", now - timedelta(hours=4, minutes=12)),
        ("KA 04 HA 2024", now - timedelta(hours=2, minutes=45)),
        ("DL 03 CC 8989", now - timedelta(hours=1, minutes=30)),
        ("MH 02 BB 3030", now - timedelta(minutes=45)),
        ("KA 05 Z 1001",  now - timedelta(minutes=15)),
    ]

    for v_no, entry_dt in active_vehicles:
        entry_str = entry_dt.strftime("%Y-%m-%d %H:%M:%S")
        ok, msg, entry_info = manager.park_vehicle(v_no, custom_entry_time=entry_str)
        if ok:
            print(f"[ACTIVE] {v_no} parked at Slot {entry_info['slot_no']} (Ticket #{entry_info['ticket_no']})")

    # Display overall stats
    stats = db.get_stats()
    print("\n=== Database Successfully Seeded! ===")
    print(f"Total Slots: {stats['total_slots']}")
    print(f"Occupied Slots: {stats['occupied_slots']}")
    print(f"Vacant Slots: {stats['vacant_slots']}")
    print(f"Historical Revenue: Rs. {stats['total_revenue']:.2f}")

if __name__ == "__main__":
    seed_sample_data(reset=True)
