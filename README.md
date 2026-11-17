    # SKY AIRWAYS — Airline Management System

    A full-stack Flask + SQLite airline management web app with a premium Tailwind CSS interface inspired by international airline booking websites.

    ## Main features

    - Premium homepage with airplane/ocean/sky style hero
    - Tailwind CSS responsive UI
    - Optional login for browsing
    - Required login for booking and personal actions
    - Signup/login with password hashing
    - Flight search and flight result cards
    - Passenger details form
    - Interactive seat selection map
    - Simulated payment module
    - Booking confirmation / boarding pass
    - Booking history
    - In-app ticket cancellation with seat availability restore
    - Check-in from Manage Booking / Booking History
    - Flight status search
    - What's on your flight page with facilities
    - Destination cards with currency selector
    - Destination detail pages
    - Loyalty dashboard
    - Feedback system
    - Admin dashboard with flight CRUD, bookings, payments and feedback overview

    ## How to run

    ```bash
    python -m venv .venv
    .venv\Scripts\activate      # Windows
    # source .venv/bin/activate  # Mac/Linux

    pip install -r requirements.txt
    python app.py
    ```

    Then open:

    ```text
    http://127.0.0.1:5000
    ```

    The SQLite database is created and seeded automatically on first run.

    ## Demo accounts

    Admin:

    ```text
    username: admin
    password: admin123
    ```

    User:

    ```text
    username: demo
    password: demo123
    ```

    ## Important authentication flow

    Visitors can browse the homepage, destinations, flight search, flight status, loyalty information, help page, about page, and what's-on-flight pages without logging in.

    Login/signup is required only for booking actions such as selecting a flight, entering passenger details, choosing a seat, simulated payment, booking history, cancellation, feedback, and admin access.

    ## Project structure

    ```text
    sky_airways_app/
    ├── app.py
    ├── requirements.txt
    ├── README.md
    ├── schema.sql
    ├── templates/
    │   ├── base.html
    │   ├── home.html
    │   ├── auth.html
    │   ├── flights.html
    │   ├── passenger.html
    │   ├── seats.html
    │   ├── payment.html
    │   ├── confirmation.html
    │   ├── history.html
    │   ├── manage.html
    │   ├── feedback.html
    │   ├── status.html
    │   ├── whats_on.html
    │   ├── destinations.html
    │   ├── destination_detail.html
    │   ├── book.html
    │   ├── loyalty.html
    │   ├── help.html
    │   ├── about.html
    │   ├── admin.html
    │   └── admin_flight_form.html
    └── static/
        ├── css/app.css
        └── js/app.js
    ```

    ## Notes

    This app uses Tailwind via CDN for fast local development. The payment system is simulated for a database course project and does not process real payments.

    ## Design correction note

    This version replaces the earlier illustration-style hero with a more realistic airline-photo hero, smaller professional typography, tighter search-panel spacing, sharper airline-style cards, and real destination photo URLs instead of gradient placeholders.
