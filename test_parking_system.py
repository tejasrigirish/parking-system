"""
Comprehensive automated test suite for Smart Parking System.
Tests database operations, duplicate entry validation, pricing logic,
slot allocation, exit releases, search, and receipts.
"""

import unittest
import os
import tempfile
from datetime import datetime, timedelta
from database import Database
from parking_manager import ParkingManager, BASE_FEE, HOURLY_RATE

class TestSmartParkingSystem(unittest.TestCase):
    def setUp(self):
        # Create a unique temporary database file for isolation
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db = Database(db_path=self.temp_db.name)
        # Re-init with 5 slots for easy edge-case testing
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM vehicle_entries;")
            conn.execute("DELETE FROM parking_slots;")
            slots = [(f"S-{i:02d}", "Vacant", None) for i in range(1, 6)]
            conn.executemany("INSERT INTO parking_slots VALUES (?, ?, ?);", slots)
            conn.commit()
        self.manager = ParkingManager(db=self.db)

    def tearDown(self):
        try:
            if os.path.exists(self.temp_db.name):
                os.remove(self.temp_db.name)
        except Exception:
            pass

    def test_01_initial_slots(self):
        """Test that initial slots are all vacant."""
        slots = self.db.get_all_slots()
        self.assertEqual(len(slots), 5)
        for s in slots:
            self.assertEqual(s["status"], "Vacant")
            self.assertIsNone(s["vehicle_no"])

    def test_02_successful_vehicle_entry(self):
        """Test successful entry and automatic slot assignment."""
        ok, msg, details = self.manager.park_vehicle("KA 01 AB 1234")
        self.assertTrue(ok)
        self.assertEqual(details["slot_no"], "S-01")
        self.assertEqual(details["vehicle_no"], "KA 01 AB 1234")
        self.assertIsNotNone(details["ticket_no"])

        # Check DB state
        slot = self.db.get_all_slots()[0]
        self.assertEqual(slot["status"], "Occupied")
        self.assertEqual(slot["vehicle_no"], "KA 01 AB 1234")

    def test_03_duplicate_entry_check(self):
        """
        CRITICAL TEST: Before allotting a slot, check if vehicle exists among currently parked entries.
        If it exists -> show 'Invalid entry, the vehicle already exists'
        """
        # First entry succeeds
        ok1, msg1, _ = self.manager.park_vehicle("KA 05 MN 9999")
        self.assertTrue(ok1)

        # Duplicate entry MUST fail with the exact specified error message
        ok2, msg2, details2 = self.manager.park_vehicle("KA 05 MN 9999")
        self.assertFalse(ok2)
        self.assertEqual(msg2, "Invalid entry, the vehicle already exists")
        self.assertIsNone(details2)

        # Case-insensitive / whitespace-insensitive check
        ok3, msg3, _ = self.manager.park_vehicle("ka 05 mn 9999")
        self.assertFalse(ok3)
        self.assertEqual(msg3, "Invalid entry, the vehicle already exists")

    def test_04_parking_full(self):
        """Test error when all slots are occupied."""
        for i in range(1, 6):
            ok, _, _ = self.manager.park_vehicle(f"KA 01 CAR {i}")
            self.assertTrue(ok)

        # 6th car should fail
        ok, msg, _ = self.manager.park_vehicle("KA 01 CAR 6")
        self.assertFalse(ok)
        self.assertIn("Parking full", msg)

    def test_05_pricing_logic_all_required_cases(self):
        """
        Verify exact required billing logic:
        - Base fare: ₹50 (covers first 1 hour only)
        - If duration <= 1 hour: Amount = ₹50
        - If duration > 1 hour: Additional Hours = ceil(duration_in_hours - 1)
                                Amount = ₹50 + (Additional Hours × ₹20)
        - ₹20 must NOT be added before the first complete hour has elapsed.

        Required Test Cases:
        30 minutes  → ₹50
        59 minutes  → ₹50
        60 minutes  → ₹50
        61 minutes  → ₹70
        90 minutes  → ₹70
        119 minutes → ₹70
        120 minutes → ₹70
        121 minutes → ₹90
        180 minutes → ₹90
        181 minutes → ₹110
        """
        entry_time = "2026-09-27 10:00:00"

        # 1. 30 minutes → ₹50
        p_30m = self.manager.calculate_pricing(entry_time, "2026-09-27 10:30:00")
        self.assertEqual(p_30m["total_amount"], 50.0)
        self.assertEqual(self.manager.calculate_fee(entry_time, "2026-09-27 10:30:00"), 50.0)

        # 2. 59 minutes → ₹50
        p_59m = self.manager.calculate_pricing(entry_time, "2026-09-27 10:59:00")
        self.assertEqual(p_59m["total_amount"], 50.0)
        self.assertEqual(self.manager.calculate_fee(entry_time, "2026-09-27 10:59:00"), 50.0)

        # 3. 60 minutes (exactly 1 hour) → ₹50
        p_60m = self.manager.calculate_pricing(entry_time, "2026-09-27 11:00:00")
        self.assertEqual(p_60m["total_amount"], 50.0)
        self.assertEqual(self.manager.calculate_fee(entry_time, "2026-09-27 11:00:00"), 50.0)

        # 4. 61 minutes (1 hour 1 minute) → ₹70
        p_61m = self.manager.calculate_pricing(entry_time, "2026-09-27 11:01:00")
        self.assertEqual(p_61m["total_amount"], 70.0)
        self.assertEqual(self.manager.calculate_fee(entry_time, "2026-09-27 11:01:00"), 70.0)

        # 5. 90 minutes (1 hour 30 minutes) → ₹70
        p_90m = self.manager.calculate_pricing(entry_time, "2026-09-27 11:30:00")
        self.assertEqual(p_90m["total_amount"], 70.0)
        self.assertEqual(self.manager.calculate_fee(entry_time, "2026-09-27 11:30:00"), 70.0)

        # 6. 119 minutes (1 hour 59 minutes) → ₹70
        p_119m = self.manager.calculate_pricing(entry_time, "2026-09-27 11:59:00")
        self.assertEqual(p_119m["total_amount"], 70.0)
        self.assertEqual(self.manager.calculate_fee(entry_time, "2026-09-27 11:59:00"), 70.0)

        # 7. 120 minutes (exactly 2 hours) → ₹70
        p_120m = self.manager.calculate_pricing(entry_time, "2026-09-27 12:00:00")
        self.assertEqual(p_120m["total_amount"], 70.0)
        self.assertEqual(self.manager.calculate_fee(entry_time, "2026-09-27 12:00:00"), 70.0)

        # 8. 121 minutes (2 hours 1 minute) → ₹90
        p_121m = self.manager.calculate_pricing(entry_time, "2026-09-27 12:01:00")
        self.assertEqual(p_121m["total_amount"], 90.0)
        self.assertEqual(self.manager.calculate_fee(entry_time, "2026-09-27 12:01:00"), 90.0)

        # 9. 180 minutes (exactly 3 hours) → ₹90
        p_180m = self.manager.calculate_pricing(entry_time, "2026-09-27 13:00:00")
        self.assertEqual(p_180m["total_amount"], 90.0)
        self.assertEqual(self.manager.calculate_fee(entry_time, "2026-09-27 13:00:00"), 90.0)

        # 10. 181 minutes (3 hours 1 minute) → ₹110
        p_181m = self.manager.calculate_pricing(entry_time, "2026-09-27 13:01:00")
        self.assertEqual(p_181m["total_amount"], 110.0)
        self.assertEqual(self.manager.calculate_fee(entry_time, "2026-09-27 13:01:00"), 110.0)

    def test_05b_pricing_edge_cases(self):
        """Test specific edge cases like 0 duration, 1 second, 1 hour 1 second, 2 hours 1 second."""
        entry_time = "2026-09-27 10:00:00"

        # 0 minutes / immediate exit
        p_0s = self.manager.calculate_pricing(entry_time, "2026-09-27 10:00:00")
        self.assertEqual(p_0s["total_amount"], 50.0)

        # 1 second
        p_1s = self.manager.calculate_pricing(entry_time, "2026-09-27 10:00:01")
        self.assertEqual(p_1s["total_amount"], 50.0)

        # 1 hour + 1 second (3601 seconds) → ₹70
        p_1h1s = self.manager.calculate_pricing(entry_time, "2026-09-27 11:00:01")
        self.assertEqual(p_1h1s["total_amount"], 70.0)

        # 2 hours + 1 second (7201 seconds) → ₹90
        p_2h1s = self.manager.calculate_pricing(entry_time, "2026-09-27 12:00:01")
        self.assertEqual(p_2h1s["total_amount"], 90.0)

    def test_06_vehicle_exit_and_slot_release(self):
        """Test vehicle exit, pricing application, and slot release back to Vacant."""
        entry_time = "2026-09-02 08:00:00"
        exit_time = "2026-09-02 11:00:00" # Exactly 3 hours: Base ₹50 + 2 addl hours × ₹20 = ₹90

        ok, _, entry_details = self.manager.park_vehicle("DL 01 XY 5678", custom_entry_time=entry_time)
        self.assertTrue(ok)
        slot_no = entry_details["slot_no"]

        # Exit vehicle
        ok_exit, msg_exit, exit_details = self.manager.exit_vehicle("DL 01 XY 5678", custom_exit_time=exit_time)
        self.assertTrue(ok_exit)
        self.assertEqual(exit_details["billed_hours"], 3)
        self.assertEqual(exit_details["additional_hours"], 2)
        self.assertEqual(exit_details["amount"], 90.0)

        # Verify exit receipt contains required fields and correct amount
        receipt = exit_details["receipt"]
        self.assertIn("Park Wave - 4 Wheeler Parking, Bangalore", receipt)
        self.assertIn("Total Amount Paid: ₹90.00", receipt)
        self.assertIn("Exit Time        : 2026-09-02 11:00:00", receipt)

        # Verify slot is vacant again
        slots = {s["slot_no"]: s for s in self.db.get_all_slots()}
        self.assertEqual(slots[slot_no]["status"], "Vacant")
        self.assertIsNone(slots[slot_no]["vehicle_no"])

        # Vehicle should now be able to park again (no longer duplicate)
        ok_reenter, _, _ = self.manager.park_vehicle("DL 01 XY 5678")
        self.assertTrue(ok_reenter)

    def test_07_search_functionality(self):
        """Test search for both parked and non-parked vehicles."""
        self.manager.park_vehicle("MH 02 BB 1111")

        # Parked search
        ok, msg, res = self.manager.search_vehicle("MH 02 BB 1111")
        self.assertTrue(ok)
        self.assertEqual(res["slot_no"], "S-01")
        self.assertEqual(res["vehicle_no"], "MH 02 BB 1111")

        # Not parked search
        ok2, msg2, res2 = self.manager.search_vehicle("DL 99 ZZ 9999")
        self.assertFalse(ok2)
        self.assertEqual(msg2, "Vehicle not found or not currently parked")
        self.assertIsNone(res2)

    def test_08_receipt_format(self):
        """Verify that the generated receipt contains all required header and fields."""
        ok, _, details = self.manager.park_vehicle("KA 03 AA 4444")
        self.assertTrue(ok)
        receipt = details["receipt"]

        # Assert mandatory receipt lines
        self.assertIn("Park Wave - 4 Wheeler Parking", receipt)
        self.assertIn("Bangalore", receipt)
        self.assertIn("Ticket No   :", receipt)
        self.assertIn("Vehicle No  : KA 03 AA 4444", receipt)
        self.assertIn("Slot No     : S-01", receipt)
        self.assertIn("Amount to Pay:", receipt)
        self.assertIn("Thank you, visit again!", receipt)

if __name__ == "__main__":
    unittest.main()
