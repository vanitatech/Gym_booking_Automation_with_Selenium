from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time

import os
from dotenv import load_dotenv
load_dotenv()

#------------------------------Step-1- Setup, Chrome Profile and Basic Navigation-----------------

# Set up Chrome profile directory
user_data_dir=os.path.join(os.getcwd(), "chrome_profile")

# Set up Chrome WebDriver
chrome_options = webdriver.ChromeOptions()

#Keep the browser open after the script finishes
#If True, you need to 'manually' QUIT Chrome before you re-run the script
chrome_options.add_experimental_option("detach", True)

#Tell Chrome Driver to use the directory to store a "profile".
chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

#Open the gym webpage
driver = webdriver.Chrome(options=chrome_options)
driver.get(os.getenv('GYM_URL'))

# Initialize WebDriverWait with a 10-second timeout
wait = WebDriverWait(driver, 10)

# ------------------------------Step-2: Retry function for network resilience ---------------------------------

# Simple retry wrapper
def retry(func, retries=7, description=None):
    for i in range(retries):
        print(f"Trying {description}. Attempt: {i+1}")
        try:
            return func()
        except TimeoutException:
            if i == retries - 1:
                raise
            time.sleep(1)

# ------------------------------Step-3: Login Function ---------------------------------

# Function to perform entire login process with retry
def login():

    # Click the login button to go to the login page
    login_btn = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
    login_btn.click()

    # Enter email address
    email_input = wait.until(EC.presence_of_element_located((By.ID, "email-input")))
    email_input.clear()
    email_input.send_keys(os.getenv('ACCOUNT_EMAIL'))

    # Enter password
    password_input = driver.find_element(By.ID, "password-input")
    password_input.clear()
    password_input.send_keys(os.getenv('ACCOUNT_PASSWORD'))

    # Click Login
    submit_btn = driver.find_element(By.ID, "submit-button")
    submit_btn.click()

    # Wait for schedule page to load
    wait.until(EC.presence_of_element_located((By.ID, "schedule-page")))

# ------------------------------Step-4: Booking Function ---------------------------------


# Function to book a class process that checks if the button text changed with retry
def book_class(booking_button):
    # Check the current button status
    current_status = booking_button.text.strip()

    # Do not click again if already booked or waitlisted
    if current_status in ("Booked", "Waitlisted"):
        return current_status

    # Determine the expected status
    if current_status not in ("Book Class", "Join Waitlist"):
        raise Exception(f"Unexpected button status: {current_status}")
    
    booking_button.click()

    # Wait for button state to change - will time out if booking failed
    wait.until(lambda d: booking_button.text.strip() in ("Booked", "Waitlisted"))
    return booking_button.text.strip()

# ---------------------------Step-5 - LOGIN ---------------------------------------------------------------

# Put the entire login flow into the retry wrapper
retry(login, description="login")

# ---------------------------Step-6 - Book EVERY TUESDAY AND THURSDAY 6PM CLASS ---------------------
# Find all class_cards:
class_cards = driver.find_elements(By.CSS_SELECTOR, "div[id^='class-card-']")



# Initialize counters for summary
booked_count = 0
waitlist_count = 0
already_booked_count = 0

# Store details of all relevant classes
processed_classes = []

#  Find every Tuesday and Thursday 6 PM class

for card in class_cards:

    # Get the day title from the parent day group
    day_group = card.find_element(By.XPATH, "./ancestor::div[contains(@id, 'day-group-')]")
    day_title = day_group.find_element(By.TAG_NAME, "h2").text

    # Check if this is a Tuesday OR Thursday
    if "Tue" in day_title or "Thu" in day_title:

        #Get the class time
        time_text = card.find_element(By.CSS_SELECTOR, "p[id^='class-time-']").text

        # Check whether the class is at 6 PM
        if "6:00 PM" in time_text:

            # Get the class name
            class_name = card.find_element(By.CSS_SELECTOR, "h3[id^='class-name-']").text

            # Find and click the book button
            button = card.find_element(By.CSS_SELECTOR, "button[id^='book-button-']")

            # Clean the day title
            clean_day = day_title.split("(")[-1].replace(")", "").strip()

            # Clean the time
            clean_time = time_text.replace("Time: ", "").strip()

            # Store class information
            class_info = {
                "name": class_name,
                "day": clean_day,
                "time": clean_time}
            
            # Check if already booked status
            button_status = button.text.strip()

            if button_status == "Booked":
                print(f"Already booked: {class_info}")
                already_booked_count += 1
                processed_classes.append(class_info)

            elif button_status == "Waitlisted":
                print(f" Already on waitlist: {class_info}")
                already_booked_count += 1
                processed_classes.append(class_info)

            elif button_status == "Book Class":
                # Use retry  for entire booking action
                result = retry(lambda: book_class(button), description="Booking")

                if result == "Booked":

                    print(f"Successfully booked: {class_info}")

                    #Book the class with retry
                    booked_count += 1
                    processed_classes.append(class_info)

                elif result == "Waitlisted":
                    print(f"Joined waitlist for: {class_info}")
                    waitlist_count += 1
                    processed_classes.append(class_info)
                time.sleep(0.5)

            elif button_status == "Join Waitlist":
                #Use retry for entire waitlist action
                result = retry(lambda: book_class(button), description="Waitlisting")

                if result == "Waitlisted":

                    print(f"Joined waitlist for: {class_info}")

                    waitlist_count += 1
                    processed_classes.append(class_info)

                elif result == "Booked":

                    print(f"Successfully booked: {class_info}")

                    booked_count += 1
                    processed_classes.append(class_info)

                time.sleep(0.5)

# --------------------- Step-7: Verify Class Bookings on My Bookings Page -------------------------

print("\n--- BOOKING SUMMARY ---")
print(f"Already booked: {already_booked_count}")
print(f"Booked: {booked_count}")
print(f"Waitlisted: {waitlist_count}")
total_booked = already_booked_count + booked_count + waitlist_count
print(f"\n--- Total Tuesday/Thursday 6pm classes: {total_booked} ---")


# --------------------- Step-8: Navigate to My Bookings Page -------------------------

# Function to navigate to my bookings with retry
def get_my_bookings():

    # Check whether we are already on the My Bookings page
    if not driver.find_elements(By.ID, "my-bookings-page"):

        my_bookings_link = wait.until(
            EC.element_to_be_clickable((By.ID, "my-bookings-link"))
        )

        my_bookings_link.click()

    # Wait for the booking cards to appear
    cards = wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "div[id*='card-']")
        )
    )

    return cards

# Navigate to my bookings with retry
all_cards = retry(get_my_bookings, description="Get my bookings")


# ------------------------------ STEP 9: VERIFY BOOKINGS ------------------------------

# Count all Tuesday / Thursday 6pm bookings
verified_count = 0

# Copy processed classes so each booking can only be verified once
remaining_bookings = processed_classes.copy()

print("\n--- VERIFYING MY BOOKINGS ---")


for card in all_cards:
    try:
        # Find the When paragraph
        when_paragraph = card.find_element(
            By.XPATH, ".//p[strong[text()='When:']]")
        when_text = when_paragraph.text

        #Find the class name
        class_name = card.find_element(By.TAG_NAME, "h3").text

        # Remove the waitlist label if present
        clean_class_name = class_name.replace(" (Waitlist)", "").strip()

        #Compare the current card with remaining bookings
        for index, booking in enumerate(remaining_bookings):
            if(
                booking["name"] == clean_class_name
                and booking["day"] in when_text
                and booking["time"] in when_text):

                print(f"Verified: {clean_class_name} - {when_text}")
                verified_count += 1

                # Remove the matched bookings to prevent duplicates
                remaining_bookings.pop(index)
                break

    except NoSuchElementException:
        pass

# ------------------------------ STEP 10: FINAL VERIFICATION RESULT ------------------------------

# Simple comparison
print(f"\n--- VERIFICATION RESULT ---")
print(f"Expected: {total_booked} bookings")
print(f"Found: {verified_count} bookings")

if total_booked == verified_count:
    print("✅ SUCCESS: All bookings verified!")
else:
    print(f"❌ MISMATCH: Missing {total_booked - verified_count} bookings")

    print("\nBookings not verified:")

    for booking in remaining_bookings:
        print(booking)

# ------------------------------ STEP 11: Close Browser ------------------------------


driver.quit()