import os
import sqlite3
import random
import string
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "sky_airways.db")

app = Flask(__name__)
app.secret_key = "sky-airways-dev-secret-change-me"

AIRPORTS = [
    "Lahore (LHE)", "Karachi (KHI)", "Islamabad (ISB)", "Dubai (DXB)", "Istanbul (IST)",
    "London (LHR)", "New York (JFK)", "Doha (DOH)", "Jeddah (JED)", "Kuala Lumpur (KUL)",
    "Paris (CDG)", "Bangkok (BKK)", "Toronto (YYZ)", "Singapore (SIN)", "Maldives (MLE)"
]

CURRENCY_RATES = {
    "PKR": 1,
    "AED": 0.013,
    "USD": 0.0036,
    "GBP": 0.0028,
    "SAR": 0.0135,
    "TRY": 0.12,
    "MYR": 0.017,
    "QAR": 0.013,
}

FACILITIES = [
    ("Cabin Comfort", "Ergonomic seats, soft lighting, and carefully tuned cabin temperature for a calmer journey."),
    ("Seat Features", "Adjustable headrests, extra legroom options, and power access on selected aircraft."),
    ("In-flight Meals", "Freshly prepared meals inspired by global cuisines with vegetarian and special-meal options."),
    ("Wi‑Fi Availability", "Stay connected above the clouds with optional onboard Wi‑Fi on long-haul aircraft."),
    ("Entertainment Screen", "Enjoy movies, music, route maps, and family entertainment through a modern seat-back system."),
    ("Baggage Allowance", "Clear baggage allowances with upgrade options during booking."),
    ("Lounge Access", "Business and First Class passengers receive priority services and lounge access where available."),
    ("Family Assistance", "Family-friendly support, priority boarding assistance, and children-friendly services."),
]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows


def execute(sql, args=()):
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur.lastrowid


def current_user():
    if session.get("user_id"):
        return query("SELECT * FROM users WHERE id = ?", (session["user_id"],), one=True)
    return None


@app.context_processor
def inject_globals():
    return {"user": current_user(), "airports": AIRPORTS, "now": datetime.now()}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("To continue with your booking, please log in or create your Sky Airways account.", "info")
            session["next_url"] = request.path
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or user["role"] != "admin":
            flash("Admin access is required.", "error")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def generate_ref(prefix="SKY"):
    return prefix + "".join(random.choices(string.ascii_uppercase + string.digits, k=7))


def init_db():
    first_run = not os.path.exists(DB_PATH)
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            country TEXT,
            date_of_birth TEXT,
            gender TEXT,
            role TEXT DEFAULT 'user',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS flights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_number TEXT UNIQUE NOT NULL,
            departure_airport TEXT NOT NULL,
            arrival_airport TEXT NOT NULL,
            departure_city TEXT NOT NULL,
            arrival_city TEXT NOT NULL,
            departure_time TEXT NOT NULL,
            arrival_time TEXT NOT NULL,
            duration TEXT NOT NULL,
            aircraft_type TEXT NOT NULL,
            cabin_class TEXT NOT NULL,
            total_seats INTEGER NOT NULL,
            available_seats INTEGER NOT NULL,
            fare REAL NOT NULL,
            status TEXT DEFAULT 'On Time'
        );
        CREATE TABLE IF NOT EXISTS seats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_id INTEGER NOT NULL,
            seat_number TEXT NOT NULL,
            seat_class TEXT NOT NULL,
            seat_status TEXT DEFAULT 'available',
            FOREIGN KEY(flight_id) REFERENCES flights(id)
        );
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            flight_id INTEGER NOT NULL,
            booking_reference TEXT UNIQUE NOT NULL,
            passenger_name TEXT NOT NULL,
            passport_or_cnic TEXT NOT NULL,
            nationality TEXT,
            phone TEXT,
            email TEXT,
            seat_number TEXT,
            cabin_class TEXT,
            fare REAL,
            booking_status TEXT DEFAULT 'Confirmed',
            payment_status TEXT DEFAULT 'Paid',
            check_in_status TEXT DEFAULT 'Not Checked In',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(flight_id) REFERENCES flights(id)
        );
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT NOT NULL,
            payment_status TEXT DEFAULT 'Paid',
            transaction_reference TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(booking_id) REFERENCES bookings(id)
        );
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            booking_id INTEGER,
            rating INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(booking_id) REFERENCES bookings(id)
        );
        CREATE TABLE IF NOT EXISTS destinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            country TEXT NOT NULL,
            image_url TEXT,
            description TEXT,
            base_fare REAL NOT NULL,
            currency TEXT DEFAULT 'PKR',
            famous_places TEXT
        );
        CREATE TABLE IF NOT EXISTS loyalty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            tier TEXT DEFAULT 'Silver',
            miles INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """
    )
    db.commit()
    user_count = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    flight_count = cur.execute("SELECT COUNT(*) FROM flights").fetchone()[0]
    destination_count = cur.execute("SELECT COUNT(*) FROM destinations").fetchone()[0]

    if user_count == 0:
        cur.execute(
            "INSERT INTO users(full_name, username, email, phone, password_hash, country, date_of_birth, gender, role) VALUES(?,?,?,?,?,?,?,?,?)",
            ("Sky Admin", "admin", "admin@skyairways.test", "+92 300 0000000", generate_password_hash("admin123"), "Pakistan", "1995-01-01", "Other", "admin"),
        )
        cur.execute(
            "INSERT INTO users(full_name, username, email, phone, password_hash, country, date_of_birth, gender, role) VALUES(?,?,?,?,?,?,?,?,?)",
            ("Demo Traveler", "demo", "demo@skyairways.test", "+92 301 1111111", generate_password_hash("demo123"), "Pakistan", "1998-05-12", "Female", "user"),
        )
        demo_id = cur.lastrowid
        cur.execute("INSERT OR IGNORE INTO loyalty(user_id, tier, miles) VALUES(?,?,?)", (demo_id, "Gold", 18400))

    if flight_count == 0:
        routes = [
            ("SK101", "Lahore (LHE)", "Dubai (DXB)", "Lahore", "Dubai", 76000, "On Time", "Airbus A320neo"),
            ("SK202", "Lahore (LHE)", "Istanbul (IST)", "Lahore", "Istanbul", 138000, "Boarding", "Boeing 787-9"),
            ("SK303", "Karachi (KHI)", "London (LHR)", "Karachi", "London", 245000, "On Time", "Boeing 777-300ER"),
            ("SK404", "Islamabad (ISB)", "New York (JFK)", "Islamabad", "New York", 382000, "Delayed", "Airbus A350"),
            ("SK505", "Lahore (LHE)", "Doha (DOH)", "Lahore", "Doha", 92000, "On Time", "Airbus A321"),
            ("SK606", "Karachi (KHI)", "Jeddah (JED)", "Karachi", "Jeddah", 105000, "Departed", "Boeing 737 MAX 8"),
            ("SK707", "Lahore (LHE)", "Kuala Lumpur (KUL)", "Lahore", "Kuala Lumpur", 158000, "On Time", "Airbus A330"),
            ("SK808", "Dubai (DXB)", "Paris (CDG)", "Dubai", "Paris", 210000, "Arrived", "Boeing 787-9"),
            ("SK909", "Lahore (LHE)", "Bangkok (BKK)", "Lahore", "Bangkok", 151000, "On Time", "Airbus A330"),
            ("SK110", "Islamabad (ISB)", "Toronto (YYZ)", "Islamabad", "Toronto", 365000, "On Time", "Boeing 777-300ER"),
            ("SK212", "Karachi (KHI)", "Singapore (SIN)", "Karachi", "Singapore", 171000, "Boarding", "Airbus A350"),
            ("SK313", "Lahore (LHE)", "Maldives (MLE)", "Lahore", "Maldives", 198000, "On Time", "Airbus A321neo"),
        ]
        cabins = ["Economy", "Premium Economy", "Business", "First Class"]
        today = datetime.now().replace(hour=8, minute=20, second=0, microsecond=0)
        for i, r in enumerate(routes):
            dep = today + timedelta(days=i % 8, hours=i * 2)
            arr = dep + timedelta(hours=3 + i % 9, minutes=25)
            cabin = cabins[i % len(cabins)]
            seats_total = 36
            last_id = cur.execute(
                """INSERT INTO flights(flight_number, departure_airport, arrival_airport, departure_city, arrival_city, departure_time, arrival_time, duration, aircraft_type, cabin_class, total_seats, available_seats, fare, status)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (r[0], r[1], r[2], r[3], r[4], dep.strftime("%Y-%m-%d %H:%M"), arr.strftime("%Y-%m-%d %H:%M"), f"{3 + i % 9}h 25m", r[7], cabin, seats_total, seats_total - 3, r[5], r[6]),
            ).lastrowid
            for row in range(1, 7):
                for col in list("ABCDEF"):
                    seat_number = f"{row}{col}"
                    seat_class = "Premium" if row <= 2 else "Standard"
                    status = "booked" if (row == 3 and col in ["A", "F"]) or (row == 5 and col == "C") else "available"
                    cur.execute("INSERT INTO seats(flight_id, seat_number, seat_class, seat_status) VALUES(?,?,?,?)", (last_id, seat_number, seat_class, status))

    destination_seed = [
        ("Dubai", "UAE", "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1000&q=82", "A skyline of innovation, luxury shopping, beaches, and desert adventures.", 76000, "Burj Khalifa|Dubai Marina|Desert Safari"),
        ("Istanbul", "Turkey", "https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?auto=format&fit=crop&w=1000&q=82", "A timeless city where continents, culture, and cuisine meet beautifully.", 138000, "Hagia Sophia|Bosphorus Cruise|Grand Bazaar"),
        ("London", "United Kingdom", "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?auto=format&fit=crop&w=1000&q=82", "Classic landmarks, royal heritage, museums, and modern neighborhoods.", 245000, "Big Ben|Tower Bridge|British Museum"),
        ("New York", "USA", "https://images.unsplash.com/photo-1485871981521-5b1fd3805eee?auto=format&fit=crop&w=1000&q=82", "A vibrant city of skyscrapers, theatres, parks, and iconic streets.", 382000, "Times Square|Central Park|Statue of Liberty"),
        ("Doha", "Qatar", "https://images.unsplash.com/photo-1518684079-3c830dcef090?auto=format&fit=crop&w=1000&q=82", "Modern architecture, premium hospitality, and peaceful coastal views.", 92000, "Museum of Islamic Art|Souq Waqif|The Pearl"),
        ("Jeddah", "Saudi Arabia", "https://images.unsplash.com/photo-1578894381163-e72c17f2d45f?auto=format&fit=crop&w=1000&q=82", "Gateway to spiritual journeys, Red Sea charm, and historic streets.", 105000, "Al-Balad|Jeddah Corniche|King Fahd Fountain"),
        ("Kuala Lumpur", "Malaysia", "https://images.unsplash.com/photo-1596422846543-75c6fc197f07?auto=format&fit=crop&w=1000&q=82", "A tropical capital with food markets, towers, and green escapes.", 158000, "Petronas Towers|Batu Caves|KLCC Park"),
        ("Paris", "France", "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=1000&q=82", "Elegant boulevards, art, fashion, and unforgettable dining experiences.", 210000, "Eiffel Tower|Louvre Museum|Montmartre"),
        ("Bangkok", "Thailand", "https://images.unsplash.com/photo-1563492065599-3520f775eeed?auto=format&fit=crop&w=1000&q=82", "Colorful temples, night markets, river life, and world-class hospitality.", 151000, "Grand Palace|Wat Arun|Chatuchak Market"),
        ("Toronto", "Canada", "https://images.unsplash.com/photo-1517935706615-2717063c2225?auto=format&fit=crop&w=1000&q=82", "A clean, diverse city with lakeside views and a global food scene.", 365000, "CN Tower|Niagara Falls|Royal Ontario Museum"),
        ("Singapore", "Singapore", "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?auto=format&fit=crop&w=1000&q=82", "A futuristic island city with gardens, luxury shopping, and clean design.", 171000, "Marina Bay Sands|Gardens by the Bay|Sentosa"),
        ("Maldives", "Maldives", "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1000&q=82", "Crystal waters, private beaches, overwater villas, and pure relaxation.", 198000, "Maafushi|Male City|Banana Reef"),
    ]
    if destination_count == 0:
        for d in destination_seed:
            cur.execute(
                "INSERT INTO destinations(city, country, image_url, description, base_fare, currency, famous_places) VALUES(?,?,?,?,?,?,?)",
                (d[0], d[1], d[2], d[3], d[4], "PKR", d[5]),
            )
    else:
        for d in destination_seed:
            cur.execute("UPDATE destinations SET image_url=?, description=?, famous_places=? WHERE city=?", (d[2], d[3], d[5], d[0]))
    db.commit()
    db.close()


@app.before_request
def ensure_db():
    init_db()


@app.route("/")
def home():
    destinations = query("SELECT * FROM destinations LIMIT 6")
    flights = query("SELECT * FROM flights ORDER BY departure_time LIMIT 5")
    return render_template("home.html", destinations=destinations, flights=flights, currencies=list(CURRENCY_RATES.keys()), facilities=FACILITIES[:4])


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if not full_name or not email or not username or not password:
            flash("Please complete all required fields.", "error")
        elif "@" not in email:
            flash("Please enter a valid email address.", "error")
        elif password != confirm:
            flash("Password and confirm password must match.", "error")
        elif query("SELECT id FROM users WHERE email=? OR username=?", (email, username), one=True):
            flash("An account with this email or username already exists.", "error")
        else:
            user_id = execute(
                """INSERT INTO users(full_name, username, email, phone, password_hash, country, date_of_birth, gender, role)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (full_name, username, email, request.form.get("phone"), generate_password_hash(password), request.form.get("country"), request.form.get("date_of_birth"), request.form.get("gender"), "user"),
            )
            execute("INSERT OR IGNORE INTO loyalty(user_id, tier, miles) VALUES(?,?,?)", (user_id, "Silver", 0))
            session["user_id"] = user_id
            flash("Welcome to Sky Airways. Your account is ready.", "success")
            next_url = session.pop("next_url", None) or request.args.get("next") or url_for("home")
            return redirect(next_url)
    return render_template("auth.html", mode="signup")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identity = request.form.get("identity", "").strip().lower()
        password = request.form.get("password", "")
        user = query("SELECT * FROM users WHERE email=? OR username=?", (identity, identity), one=True)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            flash(f"Welcome back, {user['full_name'].split()[0]}.", "success")
            next_url = session.pop("next_url", None) or request.args.get("next") or url_for("home")
            return redirect(next_url)
        flash("Invalid login details. Please try again.", "error")
    return render_template("auth.html", mode="login")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


@app.route("/flights")
def flights():
    depart = request.args.get("from") or request.args.get("departure") or ""
    arrive = request.args.get("to") or request.args.get("arrival") or ""
    cabin = request.args.get("cabin", "")
    sql = "SELECT * FROM flights WHERE 1=1"
    args = []
    if depart:
        sql += " AND departure_airport LIKE ?"
        args.append(f"%{depart}%")
    if arrive:
        sql += " AND arrival_airport LIKE ?"
        args.append(f"%{arrive}%")
    if cabin:
        sql += " AND cabin_class LIKE ?"
        args.append(f"%{cabin}%")
    sql += " ORDER BY fare ASC"
    results = query(sql, args)
    if not results:
        results = query("SELECT * FROM flights ORDER BY fare ASC LIMIT 8")
    return render_template("flights.html", flights=results, search={"from": depart, "to": arrive, "cabin": cabin})


@app.route("/select/<int:flight_id>")
def select_flight(flight_id):
    if not session.get("user_id"):
        session["selected_flight_id"] = flight_id
        session["next_url"] = url_for("passenger", flight_id=flight_id)
        flash("To continue with your booking, please log in or create your Sky Airways account.", "info")
        return redirect(url_for("login", next=url_for("passenger", flight_id=flight_id)))
    return redirect(url_for("passenger", flight_id=flight_id))


@app.route("/passenger/<int:flight_id>", methods=["GET", "POST"])
@login_required
def passenger(flight_id):
    flight = query("SELECT * FROM flights WHERE id=?", (flight_id,), one=True)
    if not flight:
        flash("Flight not found.", "error")
        return redirect(url_for("flights"))
    if request.method == "POST":
        required = ["passenger_name", "passport_or_cnic", "email", "phone"]
        if any(not request.form.get(r) for r in required):
            flash("Please complete required passenger details.", "error")
        else:
            session["passenger_details"] = dict(request.form)
            return redirect(url_for("seats", flight_id=flight_id))
    return render_template("passenger.html", flight=flight)


@app.route("/seats/<int:flight_id>", methods=["GET", "POST"])
@login_required
def seats(flight_id):
    flight = query("SELECT * FROM flights WHERE id=?", (flight_id,), one=True)
    all_seats = query("SELECT * FROM seats WHERE flight_id=? ORDER BY seat_number", (flight_id,))
    if request.method == "POST":
        seat_number = request.form.get("seat_number")
        seat = query("SELECT * FROM seats WHERE flight_id=? AND seat_number=?", (flight_id, seat_number), one=True)
        if not seat or seat["seat_status"] != "available":
            flash("Please choose an available seat.", "error")
        else:
            session["selected_seat"] = seat_number
            return redirect(url_for("payment", flight_id=flight_id))
    return render_template("seats.html", flight=flight, seats=all_seats)


@app.route("/payment/<int:flight_id>", methods=["GET", "POST"])
@login_required
def payment(flight_id):
    flight = query("SELECT * FROM flights WHERE id=?", (flight_id,), one=True)
    passenger_details = session.get("passenger_details")
    selected_seat = session.get("selected_seat")
    if not passenger_details:
        flash("Please enter passenger details first.", "error")
        return redirect(url_for("passenger", flight_id=flight_id))
    if not selected_seat:
        flash("Please select a seat first.", "error")
        return redirect(url_for("seats", flight_id=flight_id))
    if request.method == "POST":
        required = ["cardholder", "card_number", "expiry", "cvv"]
        if any(not request.form.get(r) for r in required):
            flash("Please complete payment details. This is a simulated payment.", "error")
        else:
            ref = generate_ref()
            fare = float(flight["fare"])
            booking_id = execute(
                """INSERT INTO bookings(user_id, flight_id, booking_reference, passenger_name, passport_or_cnic, nationality, phone, email, seat_number, cabin_class, fare, booking_status, payment_status, check_in_status)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (session["user_id"], flight_id, ref, passenger_details.get("passenger_name"), passenger_details.get("passport_or_cnic"), passenger_details.get("nationality"), passenger_details.get("phone"), passenger_details.get("email"), selected_seat, flight["cabin_class"], fare, "Confirmed", "Paid", "Not Checked In"),
            )
            execute("INSERT INTO payments(booking_id, amount, payment_method, payment_status, transaction_reference) VALUES(?,?,?,?,?)", (booking_id, fare, request.form.get("payment_method", "Card"), "Paid", generate_ref("TXN")))
            execute("UPDATE seats SET seat_status='booked' WHERE flight_id=? AND seat_number=?", (flight_id, selected_seat))
            execute("UPDATE flights SET available_seats=MAX(available_seats-1,0) WHERE id=?", (flight_id,))
            execute("UPDATE loyalty SET miles=miles+? WHERE user_id=?", (max(500, int(fare / 1000)), session["user_id"]))
            session.pop("passenger_details", None)
            session.pop("selected_seat", None)
            return redirect(url_for("confirmation", booking_id=booking_id))
    return render_template("payment.html", flight=flight, seat=selected_seat)


@app.route("/confirmation/<int:booking_id>")
@login_required
def confirmation(booking_id):
    booking = query("""
        SELECT b.*, f.flight_number, f.departure_airport, f.arrival_airport, f.departure_time, f.arrival_time, f.duration, f.aircraft_type
        FROM bookings b JOIN flights f ON b.flight_id=f.id WHERE b.id=? AND b.user_id=?
    """, (booking_id, session["user_id"]), one=True)
    if not booking:
        flash("Booking not found.", "error")
        return redirect(url_for("booking_history"))
    return render_template("confirmation.html", booking=booking)


@app.route("/booking-history")
@login_required
def booking_history():
    bookings = query("""
        SELECT b.*, f.flight_number, f.departure_airport, f.arrival_airport, f.departure_time, f.arrival_time, f.status AS flight_status
        FROM bookings b JOIN flights f ON b.flight_id=f.id WHERE b.user_id=? ORDER BY b.created_at DESC
    """, (session["user_id"],))
    return render_template("history.html", bookings=bookings)


@app.route("/cancel/<int:booking_id>", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    booking = query("SELECT * FROM bookings WHERE id=? AND user_id=?", (booking_id, session["user_id"]), one=True)
    if booking and booking["booking_status"] == "Confirmed":
        execute("UPDATE bookings SET booking_status='Cancelled' WHERE id=?", (booking_id,))
        execute("UPDATE seats SET seat_status='available' WHERE flight_id=? AND seat_number=?", (booking["flight_id"], booking["seat_number"]))
        execute("UPDATE flights SET available_seats=available_seats+1 WHERE id=?", (booking["flight_id"],))
        flash("Ticket cancelled. Seat availability has been restored.", "success")
    else:
        flash("This booking cannot be cancelled.", "error")
    return redirect(url_for("booking_history"))


@app.route("/manage", methods=["GET", "POST"])
@login_required
def manage_booking():
    booking = None
    if request.method == "POST":
        ref = request.form.get("booking_reference", "").strip().upper()
        last = request.form.get("last_name", "").strip().lower()
        booking = query("""
            SELECT b.*, f.flight_number, f.departure_airport, f.arrival_airport, f.departure_time, f.arrival_time
            FROM bookings b JOIN flights f ON b.flight_id=f.id WHERE b.user_id=? AND b.booking_reference=?
        """, (session["user_id"], ref), one=True)
        if not booking or (last and last not in booking["passenger_name"].lower()):
            flash("No booking matched your details.", "error")
            booking = None
    return render_template("manage.html", booking=booking)


@app.route("/check-in/<int:booking_id>", methods=["POST"])
@login_required
def check_in(booking_id):
    booking = query("SELECT * FROM bookings WHERE id=? AND user_id=?", (booking_id, session["user_id"]), one=True)
    if booking and booking["booking_status"] == "Confirmed":
        execute("UPDATE bookings SET check_in_status='Checked In' WHERE id=?", (booking_id,))
        flash("Check-in completed. Your boarding pass is ready.", "success")
    return redirect(url_for("booking_history"))


@app.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    bookings = query("SELECT * FROM bookings WHERE user_id=? ORDER BY created_at DESC", (session["user_id"],))
    if request.method == "POST":
        rating = int(request.form.get("rating", 5))
        message = request.form.get("message", "").strip()
        booking_id = request.form.get("booking_id") or None
        if not message:
            flash("Please write your feedback message.", "error")
        else:
            execute("INSERT INTO feedback(user_id, booking_id, rating, message) VALUES(?,?,?,?)", (session["user_id"], booking_id, rating, message))
            flash("Thank you. Your feedback has been submitted.", "success")
            return redirect(url_for("feedback"))
    return render_template("feedback.html", bookings=bookings)


@app.route("/status", methods=["GET", "POST"])
def status():
    result = None
    if request.method == "POST":
        flight_number = request.form.get("flight_number", "").strip().upper()
        depart = request.form.get("departure_airport", "")
        arrive = request.form.get("arrival_airport", "")
        if flight_number:
            result = query("SELECT * FROM flights WHERE flight_number=?", (flight_number,), one=True)
        elif depart or arrive:
            result = query("SELECT * FROM flights WHERE departure_airport LIKE ? AND arrival_airport LIKE ? ORDER BY departure_time LIMIT 1", (f"%{depart}%", f"%{arrive}%"), one=True)
        if not result:
            result = query("SELECT * FROM flights ORDER BY RANDOM() LIMIT 1", one=True)
    return render_template("status.html", result=result)


@app.route("/whats-on", methods=["GET", "POST"])
def whats_on():
    flight = None
    if request.method == "POST":
        fn = request.form.get("flight_number", "").strip().upper()
        depart = request.form.get("departure_airport", "")
        arrive = request.form.get("arrival_airport", "")
        if fn:
            flight = query("SELECT * FROM flights WHERE flight_number=?", (fn,), one=True)
        elif depart or arrive:
            flight = query("SELECT * FROM flights WHERE departure_airport LIKE ? AND arrival_airport LIKE ? ORDER BY departure_time LIMIT 1", (f"%{depart}%", f"%{arrive}%"), one=True)
        if not flight:
            flight = query("SELECT * FROM flights ORDER BY RANDOM() LIMIT 1", one=True)
    return render_template("whats_on.html", flight=flight, facilities=FACILITIES)


@app.route("/destinations")
def destinations():
    currency = request.args.get("currency", "PKR")
    if currency not in CURRENCY_RATES:
        currency = "PKR"
    all_destinations = query("SELECT * FROM destinations")
    return render_template("destinations.html", destinations=all_destinations, currency=currency, rate=CURRENCY_RATES[currency], currencies=CURRENCY_RATES)


@app.route("/destination/<int:destination_id>")
def destination_detail(destination_id):
    dest = query("SELECT * FROM destinations WHERE id=?", (destination_id,), one=True)
    if not dest:
        return redirect(url_for("destinations"))
    places = [p.strip() for p in dest["famous_places"].split("|")]
    return render_template("destination_detail.html", dest=dest, places=places)


@app.route("/book")
def book():
    return render_template("book.html")


@app.route("/loyalty")
def loyalty():
    loyalty_row = None
    if session.get("user_id"):
        loyalty_row = query("SELECT * FROM loyalty WHERE user_id=?", (session["user_id"],), one=True)
    return render_template("loyalty.html", loyalty=loyalty_row)


@app.route("/help")
def help_page():
    return render_template("help.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/admin")
@admin_required
def admin_dashboard():
    stats = {
        "users": query("SELECT COUNT(*) c FROM users", one=True)["c"],
        "flights": query("SELECT COUNT(*) c FROM flights", one=True)["c"],
        "bookings": query("SELECT COUNT(*) c FROM bookings", one=True)["c"],
        "revenue": query("SELECT COALESCE(SUM(amount),0) c FROM payments", one=True)["c"],
        "cancelled": query("SELECT COUNT(*) c FROM bookings WHERE booking_status='Cancelled'", one=True)["c"],
        "feedback": query("SELECT COUNT(*) c FROM feedback", one=True)["c"],
    }
    flights = query("SELECT * FROM flights ORDER BY departure_time LIMIT 8")
    bookings = query("""SELECT b.*, f.flight_number FROM bookings b JOIN flights f ON b.flight_id=f.id ORDER BY b.created_at DESC LIMIT 8""")
    feedback_rows = query("""SELECT fb.*, u.full_name FROM feedback fb JOIN users u ON fb.user_id=u.id ORDER BY fb.created_at DESC LIMIT 5""")
    return render_template("admin.html", stats=stats, flights=flights, bookings=bookings, feedback_rows=feedback_rows)


@app.route("/admin/flights/add", methods=["GET", "POST"])
@admin_required
def admin_add_flight():
    if request.method == "POST":
        values = (
            request.form.get("flight_number"), request.form.get("departure_airport"), request.form.get("arrival_airport"),
            request.form.get("departure_city"), request.form.get("arrival_city"), request.form.get("departure_time"),
            request.form.get("arrival_time"), request.form.get("duration"), request.form.get("aircraft_type"),
            request.form.get("cabin_class"), int(request.form.get("total_seats", 36)), int(request.form.get("total_seats", 36)),
            float(request.form.get("fare", 0)), request.form.get("status", "On Time")
        )
        flight_id = execute("""INSERT INTO flights(flight_number,departure_airport,arrival_airport,departure_city,arrival_city,departure_time,arrival_time,duration,aircraft_type,cabin_class,total_seats,available_seats,fare,status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", values)
        for row in range(1, 7):
            for col in "ABCDEF":
                execute("INSERT INTO seats(flight_id,seat_number,seat_class,seat_status) VALUES(?,?,?,?)", (flight_id, f"{row}{col}", "Premium" if row <= 2 else "Standard", "available"))
        flash("Flight added successfully.", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_flight_form.html", flight=None)


@app.route("/admin/flights/<int:flight_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit_flight(flight_id):
    flight = query("SELECT * FROM flights WHERE id=?", (flight_id,), one=True)
    if request.method == "POST":
        execute("""UPDATE flights SET flight_number=?, departure_airport=?, arrival_airport=?, departure_city=?, arrival_city=?, departure_time=?, arrival_time=?, duration=?, aircraft_type=?, cabin_class=?, fare=?, status=? WHERE id=?""",
                (request.form.get("flight_number"), request.form.get("departure_airport"), request.form.get("arrival_airport"), request.form.get("departure_city"), request.form.get("arrival_city"), request.form.get("departure_time"), request.form.get("arrival_time"), request.form.get("duration"), request.form.get("aircraft_type"), request.form.get("cabin_class"), float(request.form.get("fare", 0)), request.form.get("status"), flight_id))
        flash("Flight updated successfully.", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_flight_form.html", flight=flight)


@app.route("/admin/flights/<int:flight_id>/delete", methods=["POST"])
@admin_required
def admin_delete_flight(flight_id):
    execute("DELETE FROM seats WHERE flight_id=?", (flight_id,))
    execute("DELETE FROM flights WHERE id=?", (flight_id,))
    flash("Flight deleted.", "success")
    return redirect(url_for("admin_dashboard"))


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)
