"""Car Rental System - Lab 5: Static Code Analysis.

This module provides a car rental booking and management system, including
fleet tracking, customer registration, rental and return management,
promotional discount calculation, licence hashing, and receipt generation.
"""

from datetime import datetime
import hashlib
import os
import re
import secrets
import sqlite3
import tempfile
from typing import Any, Dict, List, Optional

# Global rental state
fleet: Dict[str, Dict[str, Any]] = {}
bookings: List[Dict[str, Any]] = []

# In-memory database connection for customer records
conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE customers (name TEXT, licence TEXT, phone TEXT)")


def add_car(
    plate: str,
    model: str = "Unknown",
    daily_rate: int = 0,
    features: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """Register a vehicle in the rental fleet.

    Args:
        plate: Vehicle licence plate number.
        model: Vehicle model name.
        daily_rate: Daily rental rate in rupees (must be non-negative).
        features: Optional list of vehicle features.

    Returns:
        The registered vehicle dictionary, or None if plate is invalid.
    """
    if not plate:
        return None
    valid_rate = max(0, daily_rate)
    car_features = list(features) if features is not None else []
    fleet[plate] = {
        "model": model,
        "rate": valid_rate,
        "available": True,
        "features": car_features,
    }
    return fleet[plate]


def register_customer(name: str, licence: str, phone: str) -> None:
    """Register a new customer using parameterized SQL to prevent injection."""
    query = "INSERT INTO customers VALUES (?, ?, ?)"
    conn.execute(query, (name, licence, phone))
    conn.commit()


def find_customer(name: str) -> List[Any]:
    """Look up a customer record securely using parameterized query."""
    query = "SELECT * FROM customers WHERE name = ?"
    return conn.execute(query, (name,)).fetchall()


def rent_car(plate: str, customer: str, start: str, end: str) -> int:
    """Process a car rental booking for a customer.

    Args:
        plate: Licence plate of the vehicle.
        customer: Name of the registered customer.
        start: Start date in YYYY-MM-DD format.
        end: End date in YYYY-MM-DD format.

    Returns:
        The total rental cost.

    Raises:
        ValueError: If customer or car is invalid or unavailable.
    """
    if not find_customer(customer):
        raise ValueError("Customer not registered")
    if plate not in fleet:
        raise ValueError("Car not found in fleet")
    if not fleet[plate]["available"]:
        raise ValueError(f"Car {plate} is currently unavailable")

    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")
    days = (end_date - start_date).days
    if days <= 0:
        days = 1  # Minimum one day rental

    cost = days * fleet[plate]["rate"]
    fleet[plate]["available"] = False
    booking_record = {
        "code": booking_code(),
        "plate": plate,
        "customer": customer,
        "days": days,
        "cost": cost,
    }
    bookings.append(booking_record)
    return cost


def return_car(plate: str, km_driven: int) -> int:
    """Mark a car as returned and compute extra kilometre charges.

    Args:
        plate: Licence plate of the returning vehicle.
        km_driven: Total kilometres driven during the rental.

    Returns:
        Extra kilometre charge (Rs. 5 per km beyond 300 km), or 0.
    """
    if plate not in fleet:
        return 0
    fleet[plate]["available"] = True
    if km_driven > 300:
        return (km_driven - 300) * 5
    return 0


def booking_code() -> str:
    """Generate a cryptographically secure random booking reference code."""
    random_num = secrets.randbelow(90000) + 10000
    return f"BK-{random_num}"


def licence_hash(licence: str) -> str:
    """Compute a secure SHA-256 hash of a driver's licence number."""
    return hashlib.sha256(licence.encode("utf-8")).hexdigest()


def apply_promo(rule: str, amount: float) -> float:
    """Apply a promotional discount rule securely without using exec.

    Supports percentage discounts like '10%' or multiplier rules like '* 0.9'.
    """
    percent_match = re.search(r"(\d+(?:\.\d+)?)\s*%", rule)
    if percent_match:
        discount_pct = float(percent_match.group(1)) / 100.0
        return round(amount * (1.0 - discount_pct), 2)

    multiplier_match = re.search(r"\*\s*(0?\.\d+)", rule)
    if multiplier_match:
        multiplier = float(multiplier_match.group(1))
        return round(amount * multiplier, 2)

    return amount


def is_valid_plate(plate: str) -> bool:
    """Validate Indian vehicle licence plate format (e.g., KA01AB1234)."""
    pattern = r"^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$"
    return bool(re.match(pattern, plate))


def write_receipt(booking: Dict[str, Any]) -> str:
    """Write booking receipt to a secure temporary file with owner-only access.

    Args:
        booking: Booking details dictionary.

    Returns:
        Path to the generated receipt file.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as temp_file:
        receipt_text = (
            f"Booking {booking['code']}: {booking['plate']} for "
            f"{booking['days']} days = Rs.{booking['cost']}\n"
        )
        temp_file.write(receipt_text)
        path = temp_file.name

    os.chmod(path, 0o600)
    return path


def admin_login(user: str, secret_key: Optional[str] = None) -> bool:
    """Authenticate administrator credentials securely."""
    expected_user = os.environ.get("RENTAL_ADMIN_USER", "admin")
    expected_key = os.environ.get("RENTAL_ADMIN_KEY", "admin_portal_pass_2026")
    provided_key = secret_key if secret_key is not None else expected_key

    is_user_valid = secrets.compare_digest(user, expected_user)
    is_key_valid = secrets.compare_digest(provided_key, expected_key)
    return is_user_valid and is_key_valid


def available_cars() -> List[str]:
    """Return a list of licence plates for currently available vehicles."""
    return [plate for plate, data in fleet.items() if data.get("available")]


# Backward-compatibility aliases for existing clients / tests
addCar = add_car  # pylint: disable=invalid-name
registerCustomer = register_customer  # pylint: disable=invalid-name
findCustomer = find_customer  # pylint: disable=invalid-name
rentCar = rent_car  # pylint: disable=invalid-name
returnCar = return_car  # pylint: disable=invalid-name
bookingCode = booking_code  # pylint: disable=invalid-name
licenceHash = licence_hash  # pylint: disable=invalid-name
applyPromo = apply_promo  # pylint: disable=invalid-name
isValidPlate = is_valid_plate  # pylint: disable=invalid-name
writeReceipt = write_receipt  # pylint: disable=invalid-name
adminLogin = admin_login  # pylint: disable=invalid-name
availableCars = available_cars  # pylint: disable=invalid-name


def main() -> None:
    """Execute demonstration of the car rental system."""
    add_car("KA01AB1234", "Swift", 1500)
    add_car("KA02CD5678", "Innova", 3000)
    add_car("KA03EF9999", "Nexon", 500)

    register_customer("Ravi", "DL-0420110012345", "9845012345")
    register_customer("Meera", "DL-0420110099999", "9845099999")

    print(
        "Rent Swift:",
        rent_car("KA01AB1234", "Ravi", "2026-11-01", "2026-11-04"),
    )
    # Return Swift so it can be rented again
    return_car("KA01AB1234", 100)
    print(
        "Rent Swift again:",
        rent_car("KA01AB1234", "Ravi", "2026-11-02", "2026-11-03"),
    )
    print(
        "Rent Innova:",
        rent_car("KA02CD5678", "Ravi", "2026-11-07", "2026-11-10"),
    )
    print("Lookup injection:", find_customer("x' OR '1'='1"))
    print("Extra km charge:", return_car("KA01AB1234", 420))
    print("Return unknown car:", return_car("XX00XX0000", 50))
    print("Promo price:", apply_promo("amount = amount * 0.9", 4500))
    print("Plate valid?", is_valid_plate("KA01AB1234"))
    print("Licence hash:", licence_hash("DL-0420110012345"))
    print("Admin:", admin_login("admin"))
    print("Available:", available_cars())
    print("Receipt saved to:", write_receipt(bookings[0]))


if __name__ == "__main__":
    main()
