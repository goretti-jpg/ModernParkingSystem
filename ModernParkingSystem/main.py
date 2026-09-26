from flask import Flask, render_template, request, redirect
from datetime import datetime
import math

app = Flask(__name__)

# -----------------------------
# PARKING SYSTEM SETTINGS
# -----------------------------

TOTAL_SLOTS = 50

# Management can change this through the website
PARKING_RATE = 150  # KSh per hour

# First 30 minutes are free
FREE_MINUTES = 30


# -----------------------------
# DATA STRUCTURES
# -----------------------------

# Dictionary for parking slots
# Example: {"1": "Available", "2": "KDA123A"}
parking_slots = {}

for slot_number in range(1, TOTAL_SLOTS + 1):
    parking_slots[str(slot_number)] = "Available"


# List for vehicle records
vehicle_records = []


# List for payment/audit records
payment_records = []


# -----------------------------
# HOME PAGE
# -----------------------------

@app.route("/")
def home():

    available_slots = list(
        slot for slot, status in parking_slots.items()
        if status == "Available"
    )

    occupied_slots = list(
        slot for slot, status in parking_slots.items()
        if status != "Available"
    )

    return render_template(
        "index.html",
        parking_slots=parking_slots,
        available_slots=available_slots,
        occupied_slots=occupied_slots,
        total_slots=TOTAL_SLOTS
    )


# -----------------------------
# LIVE SLOT AVAILABILITY
# -----------------------------

@app.route("/slots")
def slots():

    available_slots = [
        slot for slot, status in parking_slots.items()
        if status == "Available"
    ]

    occupied_slots = [
        slot for slot, status in parking_slots.items()
        if status != "Available"
    ]

    return render_template(
        "slots.html",
        parking_slots=parking_slots,
        total_slots=TOTAL_SLOTS,
        available_slots=available_slots,
        occupied_slots=occupied_slots
    )


# -----------------------------
# VEHICLE ENTRY
# -----------------------------

@app.route("/entry", methods=["GET", "POST"])
def vehicle_entry():

    if request.method == "POST":

        plate_number = request.form["plate_number"].strip().upper()

        # Check whether the vehicle is already inside
        for vehicle in vehicle_records:

            if (
                vehicle["plate_number"] == plate_number
                and vehicle["exit_time"] is None
            ):
                return "This vehicle is already inside the parking lot."

        # Find an available slot
        for slot_number, status in parking_slots.items():

            if status == "Available":

                # Allocate slot
                parking_slots[slot_number] = plate_number

                entry_time = datetime.now()

                vehicle = {
                    "plate_number": plate_number,
                    "slot_number": slot_number,
                    "entry_time": entry_time,
                    "exit_time": None,
                    "duration_minutes": 0,
                    "amount": 0,
                    "payment_status": "Unpaid",
                    "payment_method": None
                }

                vehicle_records.append(vehicle)

                return render_template(
                    "entry_success.html",
                    vehicle=vehicle
                )

        # No slots available
        return "Sorry, there are no available parking slots."

    return render_template("entry.html")


# -----------------------------
# VEHICLE EXIT
# -----------------------------

@app.route("/exit", methods=["GET", "POST"])
def vehicle_exit():

    if request.method == "POST":

        plate_number = request.form["plate_number"].strip().upper()

        for vehicle in vehicle_records:

            if (
                vehicle["plate_number"] == plate_number
                and vehicle["exit_time"] is None
            ):

                exit_time = datetime.now()

                duration = exit_time - vehicle["entry_time"]

                duration_minutes = int(
                    duration.total_seconds() / 60
                )

                vehicle["exit_time"] = exit_time
                vehicle["duration_minutes"] = duration_minutes

                # -----------------------------
                # CALCULATE PARKING FEE
                # -----------------------------

                if duration_minutes <= FREE_MINUTES:

                    amount = 0

                else:

                    chargeable_minutes = (
                        duration_minutes - FREE_MINUTES
                    )

                    hours = math.ceil(
                        chargeable_minutes / 60
                    )

                    amount = hours * PARKING_RATE

                vehicle["amount"] = amount

                return redirect(
                    f"/payment/{plate_number}/{amount}"
                )

        return "Vehicle not found or vehicle has already exited."

    return render_template("exit.html")


# -----------------------------
# PAYMENT
# -----------------------------

@app.route(
    "/payment/<plate_number>/<int:amount>",
    methods=["GET", "POST"]
)
def payment(plate_number, amount):

    for vehicle in vehicle_records:

        if vehicle["plate_number"] == plate_number:

            # Payment submitted
            if request.method == "POST":

                payment_method = request.form["payment_method"]

                vehicle["payment_status"] = "Paid"
                vehicle["payment_method"] = payment_method

                # Create an audit/payment record
                payment_record = {
                    "plate_number": vehicle["plate_number"],
                    "slot_number": vehicle["slot_number"],
                    "amount": vehicle["amount"],
                    "payment_method": payment_method,
                    "payment_time": datetime.now()
                }

                payment_records.append(payment_record)

                # Release parking slot
                parking_slots[
                    vehicle["slot_number"]
                ] = "Available"

                return render_template(
                    "payment_success.html",
                    plate_number=vehicle["plate_number"],
                    slot_number=vehicle["slot_number"],
                    amount=vehicle["amount"],
                    payment_method=payment_method
                )

            # Show payment page
            return render_template(
                "payment.html",
                vehicle=vehicle,
                amount=amount
            )

    return "Vehicle not found."


# -----------------------------
# ADMINISTRATIVE REPORT
# -----------------------------

@app.route("/reports")
def reports():

    total_collected = sum(
        record["amount"]
        for record in payment_records
    )

    return render_template(
        "reports.html",
        vehicle_records=vehicle_records,
        payment_records=payment_records,
        total_collected=total_collected
    )


# -----------------------------
# CHANGE PARKING RATE
# -----------------------------

@app.route("/settings", methods=["GET", "POST"])
def settings():

    global PARKING_RATE

    if request.method == "POST":

        new_rate = request.form["parking_rate"]

        try:
            new_rate = float(new_rate)

            if new_rate <= 0:
                return "Parking rate must be greater than zero."

            PARKING_RATE = new_rate

            return render_template(
                "settings.html",
                parking_rate=PARKING_RATE,
                message="Parking rate updated successfully."
            )

        except ValueError:

            return "Please enter a valid parking rate."

    return render_template(
        "settings.html",
        parking_rate=PARKING_RATE
    )


# -----------------------------
# RUN APPLICATION
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True)