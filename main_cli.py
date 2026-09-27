"""
Interactive Command-Line Interface (CLI) for Smart Parking System.
Provides full menu-driven terminal interaction for slot allocation, duplicate checks,
search, pricing, receipt generation, and slot map display.
"""

import sys
import os

# Configure console encoding for Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from datetime import datetime
from typing import Optional
from database import Database
from parking_manager import ParkingManager

def print_banner():
    print("=" * 60)
    print("       PARK WAVE - 4 WHEELER SMART PARKING SYSTEM       ")
    print("                     Bangalore                          ")
    print("=" * 60)

def display_slots_grid(db: Database):
    slots = db.get_all_slots()
    print("\n--- Current Parking Slots Status ---")
    print("-" * 52)
    print(f"{'Slot No':<10} | {'Status':<12} | {'Occupied By':<24}")
    print("-" * 52)
    for s in slots:
        status = s["status"]
        veh = s["vehicle_no"] or "---"
        status_display = "[OCCUPIED]" if status == "Occupied" else "[VACANT]  "
        print(f"{s['slot_no']:<10} | {status_display:<12} | {veh:<24}")
    print("-" * 52)

def handle_entry(manager: ParkingManager):
    print("\n>>> VEHICLE ENTRY <<<")
    vehicle_no = input("Enter Vehicle Number (e.g. KA 01 AB 1234): ").strip()
    if not vehicle_no:
        print("[!] Vehicle number cannot be empty.")
        return

    ok, msg, details = manager.park_vehicle(vehicle_no)
    if not ok:
        print(f"\n[ERROR] {msg}")
        return

    print(f"\n[SUCCESS] {msg}")
    print("\n" + details["receipt"] + "\n")

def handle_exit(manager: ParkingManager):
    print("\n>>> VEHICLE EXIT & BILLING <<<")
    identifier = input("Enter Vehicle Number or Ticket No: ").strip()
    if not identifier:
        print("[!] Input cannot be empty.")
        return

    ok, msg, details = manager.exit_vehicle(identifier)
    if not ok:
        print(f"\n[ERROR] {msg}")
        return

    print(f"\n[SUCCESS] {msg}")
    print("\n--- Final Bill & Receipt ---")
    print(manager.generate_detailed_exit_bill(details))
    print()

def handle_search(manager: ParkingManager):
    print("\n>>> SEARCH VEHICLE <<<")
    vehicle_no = input("Enter Vehicle Number to Search: ").strip()
    if not vehicle_no:
        print("[!] Input cannot be empty.")
        return

    ok, msg, details = manager.search_vehicle(vehicle_no)
    if not ok:
        print(f"\n[!] {msg}")
        return

    print(f"\n[FOUND] Vehicle Details:")
    print(f"  • Vehicle No     : {details['vehicle_no']}")
    print(f"  • Allocated Slot : {details['slot_no']}")
    print(f"  • Ticket No      : #{details['ticket_no']}")
    print(f"  • Entry Timestamp: {details['entry_time']}")
    print(f"  • Time Parked    : {details.get('current_duration', 'N/A')}")
    print(f"  • Est. Amount Due: Rs. {details.get('estimated_amount', 50.0):.2f}")

def handle_active_entries(db: Database, manager: Optional[ParkingManager] = None):
    active = db.get_all_active_entries()
    print(f"\n--- Currently Parked Vehicles ({len(active)}) ---")
    if not active:
        print("No vehicles currently parked.")
        return

    print("-" * 86)
    print(f"{'Ticket':<8} | {'Vehicle No':<16} | {'Slot No':<8} | {'Entry Time':<20} | {'Current Fee':<12} | {'Duration':<10}")
    print("-" * 86)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for row in active:
        if manager:
            p = manager.calculate_pricing(row['entry_time'], now_str)
            fee_str = f"Rs. {p['total_amount']:.2f}"
            dur_str = p['duration_str']
        else:
            fee_str = "Rs. 50.00"
            dur_str = "N/A"
        print(f"#{row['ticket_no']:<7} | {row['vehicle_no']:<16} | {row['slot_no']:<8} | {row['entry_time']:<20} | {fee_str:<12} | {dur_str:<10}")
    print("-" * 86)

def handle_stats(db: Database):
    stats = db.get_stats()
    print("\n--- System Summary & Statistics ---")
    print(f"  • Total Parking Bays   : {stats['total_slots']}")
    print(f"  • Occupied Slots       : {stats['occupied_slots']}")
    print(f"  • Available Vacant     : {stats['vacant_slots']}")
    print(f"  • Completed Exits      : {stats['total_completed_exits']}")
    print(f"  • Total Revenue Earned : Rs. {stats['total_revenue']:.2f}")

def main():
    db = Database()
    manager = ParkingManager(db=db)

    while True:
        print_banner()
        print("1. Vehicle Entry (Allot Next Vacant Slot)")
        print("2. Vehicle Exit & Calculate Bill")
        print("3. Search Parked Vehicle by Plate No")
        print("4. View Slot-Wise Status Grid")
        print("5. View All Active Parked Vehicles")
        print("6. View Overall System Statistics & Revenue")
        print("7. Launch in Separate Desktop Window (GUI)")
        print("0. Exit Application")
        print("-" * 60)

        choice = input("Select an option [0-7]: ").strip()

        if choice == "1":
            handle_entry(manager)
        elif choice == "2":
            handle_exit(manager)
        elif choice == "3":
            handle_search(manager)
        elif choice == "4":
            display_slots_grid(db)
        elif choice == "5":
            handle_active_entries(db, manager)
        elif choice == "6":
            handle_stats(db)
        elif choice == "7":
            print("\nLaunching graphical application in a separate window...")
            try:
                from app_gui import run_app
                run_app()
            except Exception as e:
                print(f"[!] Could not launch GUI: {e}")
        elif choice == "0":
            print("\nThank you for using Park Wave Smart Parking System!")
            break
        else:
            print("\n[!] Invalid choice. Please choose between 0 and 7.")

        input("\nPress Enter to return to menu...")
        print("\n" * 2)

if __name__ == "__main__":
    main()
