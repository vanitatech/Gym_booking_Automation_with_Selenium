# Gym Class Booking Automation

This Selenium script signs in to the configured gym booking site, books or joins the waitlist for every Tuesday and Thursday 6:00 PM class it finds, and checks the resulting bookings on the My Bookings page.

## Requirements

- Python 3.8 or newer
- Google Chrome or Chromium
- Selenium and python-dotenv

Install the Python dependencies:

```bash
python -m pip install selenium python-dotenv
```

Selenium Manager can locate or download a compatible browser driver. You need a working Chrome or Chromium installation.

## Configuration

Create a `.env` file next to `main.py`:

```dotenv
GYM_URL=https://your-gym-booking-site.example
ACCOUNT_EMAIL=your-account-email
ACCOUNT_PASSWORD=your-account-password
```

Use the booking URL and credentials for an account you are authorized to access. The script stores a persistent Chrome session in `chrome_profile/`; treat that directory as sensitive and do not share it.

## Run

From this directory, run:

```bash
python main.py
```

The script books matching classes or joins their waitlists and reports whether it can verify the results. Review the selected class details and the site's booking rules before running it.
