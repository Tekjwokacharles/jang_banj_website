# JANG BANJ Construction & Engineering Website

A Flask + SQLite starter website inspired by the supplied JANG BANJ construction designs.

## Features
- Responsive company homepage
- Construction services and projects sections
- Dynamic construction price list
- SQLite database
- Admin login
- Add, edit and delete price items
- Add price categories
- Supplied reference images included as assets

## Run on Windows

1. Install Python.
2. Open Command Prompt in this folder.
3. Create a virtual environment:

   python -m venv venv

4. Activate it:

   venv\Scripts\activate

5. Install dependencies:

   pip install -r requirements.txt

6. Start the website:

   python app.py

7. Open:

   http://127.0.0.1:5000

## Admin

Open:

http://127.0.0.1:5000/admin/login

Demo credentials:
- Username: admin
- Password: admin123

IMPORTANT: Change the secret key and admin authentication before deploying this publicly.

## Next development steps
- Replace placeholder contact details.
- Add real project gallery management.
- Add company profile management.
- Add image upload.
- Add PDF price-list generation.
- Add WhatsApp sharing.
- Add proper admin users/password hashing.
- Deploy to Render or another production platform.
