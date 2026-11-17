✈️ Sky Airways — Airline Management System
A full-stack Flask + SQLite airline management web app with a premium Tailwind CSS interface inspired by international airline booking websites like Emirates and AirSial. It delivers a complete end-to-end booking experience — from flight search and interactive seat selection to simulated payment and boarding pass generation.

✨ Main Features
For Passengers

Premium homepage with airplane/ocean/sky hero

Responsive Tailwind CSS UI

Optional login for browsing; required login for booking

Secure signup/login with password hashing

Flight search with result cards

Passenger details form

Interactive seat selection map

Simulated payment module

Booking confirmation / boarding pass

Booking history with ticket cancellation (restores seats)

Check-in from Manage Booking / Booking History

Flight status search

"What's on your flight" page with facilities

Destination cards with currency selector and detail pages

Loyalty dashboard

Feedback system

For Administrators

Admin dashboard with flight CRUD

Bookings, payments, and feedback overview

🔐 Authentication Flow
Visitors can browse the homepage, destinations, flight search, flight status, loyalty info, help, about, and what's-on-flight pages without logging in.

Login/signup is required only for booking actions — selecting a flight, entering passenger details, choosing a seat, simulated payment, booking history, cancellation, feedback, and admin access.

🚀 How to Run
Create and activate a virtual environment, install the required packages, then start the app:

bash
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Mac/Linux

pip install -r requirements.txt
python app.py
Then open http://127.0.0.1:5000 in your browser. The SQLite database is created and seeded automatically on first run.

👤 Demo Accounts
Admin — username: admin | password: admin123

User — username: demo | password: demo123

📁 Project Structure
The app follows a clean Flask layout: app.py holds the application logic, schema.sql defines the database, requirements.txt lists dependencies, templates/ contains all HTML pages (home, auth, flights, passenger, seats, payment, confirmation, history, manage, feedback, status, whats_on, destinations, destination_detail, book, loyalty, help, about, admin, and admin_flight_form), and static/ holds css/app.css and js/app.js.

📝 Notes
Tailwind is loaded via CDN for fast local development. The payment system is simulated for a database course project and does not process real payments. This version replaces the earlier illustration-style hero with a more realistic airline-photo hero, smaller professional typography, tighter search-panel spacing, sharper airline-style cards, and real destination photo URLs instead of gradient placeholders.

🎯 Purpose
Sky Airways was built as a database course project to showcase practical implementation of authentication, database design, session handling, dynamic UI, and admin management — and it serves as a strong foundation for a production-ready airline booking system.

📄 License
MIT License — free to use, learn from, and build upon.
