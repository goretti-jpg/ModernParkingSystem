from flask import Flask, render_template,request, redirect
from datetime import datetime

app = Flask(__name__)

TOTAL_SLOTS = 50

parking_slots = {}


for slot_number in range(1, TOTAL_SLOTS + 1):
    parking_slots[str(slot_number)] = "Available"

vehicle_records = []

@app.route("/")
def home():
    return render_template("index.html", parking_slots=parking_slots)

@app.route("/slots")
def slots():
    occupied_slots = [record.slot_number for record in parking_records]

    return render_template(
        "slots.html",
        total_slots=total_parking_slots,
        available_slots=available_parking_slots,
        occupied_slots=occupied_slots
    )
#Vehicle entry
@app.route("/entry", methods=["GET", "POST"])
def vehicle_entry():

    if request.method == "POST":

        plate_number = request.form["plate_number"]

        for slot_number, status in parking_slots.items():

            if status == "Available":

                parking_slots[slot_number] = plate_number

                entry_time = datetime.now()

                vehicle = {
                    "plate_number": plate_number,
                    "slot_number": slot_number,
                    "entry_time": entry_time,
                    "exit_time": None,
                    "duration_minutes": 0,
                    "amount": 0,
                    "payment_status": "Unpaid"
                }

                vehicle_records.append(vehicle)

                return f"Vehicle {plate_number} has been assigned Slot {slot_number}."

        return "Sorry, there are no available parking slots."

    return render_template("entry.html")

@app.route("/exit", methods=["GET", "POST"])
def vehicle_exit():

    if request.method == "POST":

        plate_number = request.form["plate_number"]

        for vehicle in vehicle_records:

            if vehicle["plate_number"] == plate_number:

                exit_time = datetime.now()

                duration = exit_time - vehicle["entry_time"]

                duration_minutes = int(duration.total_seconds() / 60)

                vehicle["exit_time"] = exit_time
                vehicle["duration_minutes"] = duration_minutes

                if duration_minutes <= 30:
                    amount = 0

                elif duration_minutes <= 120:
                    amount = 50

                elif duration_minutes <= 240:
                    amount = 100

                elif duration_minutes <= 360:
                    amount = 300

                else:
                    amount = 500

                vehicle["amount"] = amount

                return redirect(f"/payment/{plate_number}/{amount}")
        return "Vehicle not found."

    return render_template("exit.html")

@app.route("/payment/<plate_number>/<int:amount>", methods=["GET", "POST"])
def payment(plate_number, amount):

    # Find the vehicle
    for vehicle in vehicle_records:

        if vehicle["plate_number"] == plate_number:

                # If payment button is clicked
                if request.method == "POST":

                    vehicle["payment_status"] = "Paid"

                    # Release the parking slot
                    parking_slots[vehicle["slot_number"]] = "Available"

                    return render_template(
    "payment_success.html",
                    plate_number=vehicle["plate_number"],
                    slot_number=vehicle["slot_number"] )

                # Show the payment page
                return render_template(
    "payment.html",
                    vehicle=vehicle,
                    amount=amount )
    return "Vehicle not found."

if __name__ == "__main__":
    app.run(debug=True)