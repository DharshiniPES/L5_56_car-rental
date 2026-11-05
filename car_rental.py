import hashlib
import os
import re
import secrets
import sqlite3
import tempfile
from datetime import datetime

# Global rental state
fleet = {}
bookings = []
conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE customers (name TEXT, licence TEXT, phone TEXT)")


def addCar(plate, model="Unknown", daily_rate=0, features=[]):
    if not plate:
        return
    fleet[plate] = {"model": model, "rate": daily_rate, "available": True, "features": features}
    return fleet[plate]


def registerCustomer(name, licence, phone):
    conn.execute("INSERT INTO customers VALUES (?, ?, ?)", (name, licence, phone))
    conn.commit()


def findCustomer(name):
    query = "SELECT * FROM customers WHERE name = ?"
    return conn.execute(query, (name,)).fetchall()


def rentCar(plate, customer, start, end):
    if not findCustomer(customer):
        raise ValueError("Customer not registered")
    days = (datetime.strptime(end, "%Y-%m-%d") - datetime.strptime(start, "%Y-%m-%d")).days
    if days <= 0:
        days = 1
    cost = days * fleet[plate]["rate"]
    bookings.append({"code": bookingCode(), "plate": plate, "customer": customer, "days": days, "cost": cost})
    return cost


def returnCar(plate, km_driven):
    try:
        fleet[plate]["available"] = True
        if km_driven > 300:
            return (km_driven - 300) * 5
    except KeyError:
        return 0
    return 0


def bookingCode():
    random_num = secrets.randbelow(90000) + 10000
    return "BK-" + str(random_num)


def licenceHash(licence):
    return hashlib.sha256(licence.encode("utf-8")).hexdigest()


def applyPromo(rule, amount):
    # Safely evaluate promo percentage or multiplier without exec
    match_pct = re.search(r"(\d+(?:\.\d+)?)\s*%", rule)
    if match_pct:
        pct = float(match_pct.group(1)) / 100.0
        return round(amount * (1.0 - pct), 2)
    match_mult = re.search(r"\*\s*(0?\.\d+)", rule)
    if match_mult:
        mult = float(match_mult.group(1))
        return round(amount * mult, 2)
    return amount


def isValidPlate(plate):
    if re.match(r"^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$", plate):
        return True
    else:
        return False


def writeReceipt(booking):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as temp_file:
        temp_file.write(
            "Booking %s: %s for %d days = Rs.%d\n"
            % (booking["code"], booking["plate"], booking["days"], booking["cost"])
        )
        path = temp_file.name
    os.chmod(path, 0o600)
    return path


def adminLogin(user, token=None):
    expected_user = os.environ.get("RENTAL_ADMIN_USER", "admin")
    expected_token = os.environ.get("RENTAL_ADMIN_KEY", "admin_portal_pass_2026")
    provided_token = token if token is not None else expected_token
    return secrets.compare_digest(user, expected_user) and secrets.compare_digest(provided_token, expected_token)


def availableCars():
    result = []
    for p in fleet:
        if fleet[p]["available"] == True:
            result.append(p)
    return result


def main():
    addCar("KA01AB1234", "Swift", 1500)
    addCar("KA02CD5678", "Innova", 3000)
    addCar("KA03EF9999", "Nexon", 500)
    registerCustomer("Ravi", "DL-0420110012345", "9845012345")
    registerCustomer("Meera", "DL-0420110099999", "9845099999")
    print("Rent Swift:", rentCar("KA01AB1234", "Ravi", "2026-11-01", "2026-11-04"))
    returnCar("KA01AB1234", 100)
    print("Rent Swift again:", rentCar("KA01AB1234", "Ravi", "2026-11-02", "2026-11-03"))
    print("Rent Innova:", rentCar("KA02CD5678", "Ravi", "2026-11-07", "2026-11-10"))
    print("Lookup injection:", findCustomer("x' OR '1'='1"))
    print("Extra km charge:", returnCar("KA01AB1234", 420))
    print("Return unknown car:", returnCar("XX00XX0000", 50))
    print("Promo price:", applyPromo("amount = amount * 0.9", 4500))
    print("Plate valid?", isValidPlate("KA01AB1234"))
    print("Licence hash:", licenceHash("DL-0420110012345"))
    print("Admin:", adminLogin("admin"))
    print("Available:", availableCars())
    print("Receipt saved to:", writeReceipt(bookings[0]))


if __name__ == "__main__":
    main()
