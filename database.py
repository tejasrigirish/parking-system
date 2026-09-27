"""
Database layer for the Smart Parking System.
Manages SQLite operations, table schema creation, slot allocation, and transaction integrity.
"""

import sqlite3
import os
import contextlib
from typing import List, Dict, Optional, Tuple, Any

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "parking_system.db")

class Database:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.init_db()

    @contextlib.contextmanager
    def get_connection(self):
        """Create and return a database connection with row factory and foreign keys enabled, cleanly closing on exit."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self, total_slots: int = 20) -> None:
        """Initialize database schema and populate initial slots if empty."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create parking_slots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parking_slots (
                    slot_no TEXT PRIMARY KEY,
                    status TEXT NOT NULL CHECK(status IN ('Occupied', 'Vacant')),
                    vehicle_no TEXT DEFAULT NULL
                );
            """)

            # Create vehicle_entries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vehicle_entries (
                    ticket_no INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_no TEXT NOT NULL,
                    slot_no TEXT NOT NULL,
                    entry_time TEXT NOT NULL,
                    exit_time TEXT DEFAULT NULL,
                    amount REAL DEFAULT NULL,
                    FOREIGN KEY (slot_no) REFERENCES parking_slots(slot_no)
                );
            """)

            # Create performance indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_entries_vehicle_active 
                ON vehicle_entries (vehicle_no, exit_time);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_slots_status 
                ON parking_slots (status);
            """)

            # Populate slots if table is empty
            cursor.execute("SELECT COUNT(*) FROM parking_slots;")
            count = cursor.fetchone()[0]
            if count == 0:
                slots = [(f"S-{i:02d}", "Vacant", None) for i in range(1, total_slots + 1)]
                cursor.executemany(
                    "INSERT INTO parking_slots (slot_no, status, vehicle_no) VALUES (?, ?, ?);",
                    slots
                )
            conn.commit()

    def clear_all_data(self, total_slots: int = 20) -> None:
        """Reset all tables: empty vehicle entries and make all parking bays vacant."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vehicle_entries;")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='vehicle_entries';")
            cursor.execute("DELETE FROM parking_slots;")
            slots = [(f"S-{i:02d}", "Vacant", None) for i in range(1, total_slots + 1)]
            cursor.executemany(
                "INSERT INTO parking_slots (slot_no, status, vehicle_no) VALUES (?, ?, ?);",
                slots
            )
            conn.commit()

    def get_all_slots(self) -> List[Dict[str, Any]]:
        """Retrieve all slots sorted by slot number."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT slot_no, status, vehicle_no FROM parking_slots ORDER BY slot_no ASC;")
            return [dict(row) for row in cursor.fetchall()]

    def get_next_vacant_slot(self) -> Optional[str]:
        """Find the next available vacant slot."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT slot_no FROM parking_slots WHERE status = 'Vacant' ORDER BY slot_no ASC LIMIT 1;"
            )
            row = cursor.fetchone()
            return row["slot_no"] if row else None

    def get_active_entry_by_vehicle(self, vehicle_no: str) -> Optional[Dict[str, Any]]:
        """Check if a vehicle is currently parked (active entry where exit_time is NULL)."""
        clean_vehicle = vehicle_no.strip().upper()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ticket_no, vehicle_no, slot_no, entry_time, exit_time, amount
                FROM vehicle_entries
                WHERE UPPER(vehicle_no) = ? AND exit_time IS NULL
                ORDER BY ticket_no DESC LIMIT 1;
                """,
                (clean_vehicle,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_active_entry_by_ticket(self, ticket_no: int) -> Optional[Dict[str, Any]]:
        """Retrieve an active entry by ticket number."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ticket_no, vehicle_no, slot_no, entry_time, exit_time, amount
                FROM vehicle_entries
                WHERE ticket_no = ? AND exit_time IS NULL;
                """,
                (ticket_no,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def allocate_slot_and_create_entry(self, vehicle_no: str, slot_no: str, entry_time: str) -> int:
        """
        Atomically mark the slot as Occupied and create the entry record.
        Returns the generated ticket_no.
        """
        clean_vehicle = vehicle_no.strip().upper()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # 1. Update slot status to Occupied
            cursor.execute(
                "UPDATE parking_slots SET status = 'Occupied', vehicle_no = ? WHERE slot_no = ? AND status = 'Vacant';",
                (clean_vehicle, slot_no)
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Slot {slot_no} is no longer vacant or does not exist.")

            # 2. Insert into vehicle_entries
            cursor.execute(
                """
                INSERT INTO vehicle_entries (vehicle_no, slot_no, entry_time, exit_time, amount)
                VALUES (?, ?, ?, NULL, NULL);
                """,
                (clean_vehicle, slot_no, entry_time)
            )
            ticket_no = cursor.lastrowid
            conn.commit()
            return ticket_no

    def complete_exit(self, ticket_no: int, slot_no: str, exit_time: str, amount: float) -> bool:
        """
        Atomically complete vehicle exit:
        1. Updates vehicle_entries with exit_time and amount.
        2. Sets slot status back to 'Vacant' and clears vehicle_no.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Update vehicle_entries
            cursor.execute(
                """
                UPDATE vehicle_entries
                SET exit_time = ?, amount = ?
                WHERE ticket_no = ? AND exit_time IS NULL;
                """,
                (exit_time, amount, ticket_no)
            )
            if cursor.rowcount == 0:
                return False

            # Free up parking slot
            cursor.execute(
                "UPDATE parking_slots SET status = 'Vacant', vehicle_no = NULL WHERE slot_no = ?;",
                (slot_no,)
            )
            conn.commit()
            return True

    def search_vehicle(self, vehicle_no: str) -> Optional[Dict[str, Any]]:
        """
        Search for a vehicle currently parked.
        Returns dictionary with ticket_no, vehicle_no, slot_no, entry_time, status.
        """
        clean_vehicle = vehicle_no.strip().upper()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT e.ticket_no, e.vehicle_no, e.slot_no, e.entry_time, s.status
                FROM vehicle_entries e
                JOIN parking_slots s ON e.slot_no = s.slot_no
                WHERE UPPER(e.vehicle_no) = ? AND e.exit_time IS NULL
                ORDER BY e.ticket_no DESC LIMIT 1;
                """,
                (clean_vehicle,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_active_entries(self) -> List[Dict[str, Any]]:
        """List all currently parked vehicles."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ticket_no, vehicle_no, slot_no, entry_time
                FROM vehicle_entries
                WHERE exit_time IS NULL
                ORDER BY entry_time DESC;
                """
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve recent parking history (both active and completed)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ticket_no, vehicle_no, slot_no, entry_time, exit_time, amount
                FROM vehicle_entries
                ORDER BY ticket_no DESC
                LIMIT ?;
                """,
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        """Compute aggregate system statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM parking_slots;")
            total_slots = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) as occupied FROM parking_slots WHERE status = 'Occupied';")
            occupied_slots = cursor.fetchone()["occupied"]

            cursor.execute("SELECT COALESCE(SUM(amount), 0.0) as revenue FROM vehicle_entries WHERE amount IS NOT NULL;")
            total_revenue = cursor.fetchone()["revenue"]

            cursor.execute("SELECT COUNT(*) as completed FROM vehicle_entries WHERE exit_time IS NOT NULL;")
            total_exited = cursor.fetchone()["completed"]

            return {
                "total_slots": total_slots,
                "occupied_slots": occupied_slots,
                "vacant_slots": total_slots - occupied_slots,
                "total_revenue": total_revenue,
                "total_completed_exits": total_exited,
            }
