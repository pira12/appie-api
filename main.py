import creds
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from pprint import pprint
from Google import Create_Service, convert_to_RFC_datetime
from datetime import datetime, timedelta
import time
import schedule
from webdriver_manager.chrome import ChromeDriverManager

# List of pay dates in a structured format
PAYDATES = [
    {"date": "maandag 8 januari 2024", "description": "Uitbetaaldatum periode 13 2023"},
    {"date": "maandag 5 februari 2024", "description": "Inclusief personeelskorting"},
    {"date": "maandag 4 maart 2024", "description": ""},
    {"date": "dinsdag 2 april 2024", "description": "Inclusief aanvullende winstuitkering"},
    {"date": "maandag 29 april 2024", "description": "Inclusief personeelskorting en vakantiegeld"},
    {"date": "maandag 27 mei 2024", "description": ""},
    {"date": "maandag 24 juni 2024", "description": ""},
    {"date": "maandag 22 juli 2024", "description": "Inclusief personeelskorting"},
    {"date": "maandag 19 augustus 2024", "description": ""},
    {"date": "maandag 16 september 2024", "description": "P9"},
    {"date": "maandag 14 oktober 2024", "description": ""},
    {"date": "maandag 11 november 2024", "description": "Inclusief personeelskorting"},
    {"date": "maandag 9 december 2024", "description": ""},
    {"date": "maandag 6 januari 2025", "description": "Salaris P13 2024"},
]

# Mapping of Dutch days to English
DUTCH_TO_ENGLISH_DAYS = {
    "maandag": "Monday",
    "dinsdag": "Tuesday",
    "woensdag": "Wednesday",
    "donderdag": "Thursday",
    "vrijdag": "Friday",
    "zaterdag": "Saturday",
    "zondag": "Sunday"
}

# Mapping of Dutch months to English
DUTCH_TO_ENGLISH_MONTHS = {
    "januari": "January",
    "februari": "February",
    "maart": "March",
    "april": "April",
    "mei": "May",
    "juni": "June",
    "juli": "July",
    "augustus": "August",
    "september": "September",
    "oktober": "October",
    "november": "November",
    "december": "December"
}

def translate_dutch_date(dutch_date):
    """Translate a Dutch date string into an English date string."""
    # Replace day names
    for dutch_day, english_day in DUTCH_TO_ENGLISH_DAYS.items():
        if dutch_day in dutch_date:
            dutch_date = dutch_date.replace(dutch_day, english_day)

    # Replace month names
    for dutch_month, english_month in DUTCH_TO_ENGLISH_MONTHS.items():
        if dutch_month in dutch_date:
            dutch_date = dutch_date.replace(dutch_month, english_month)

    return dutch_date

def add_paydates_to_calendar(service):
    """Add predefined pay dates to the calendar as all-day events."""
    calendar_id = get_calendar_id(service, 'AH Werkrooster')

    if not calendar_id:
        print("Unable to add pay dates: Calendar ID not found.")
        return  # Exit function if calendar_id is None

    for paydate in PAYDATES:
        # Translate Dutch date to English
        translated_date = translate_dutch_date(paydate["date"])

        # Parse the date string into a datetime object
        pay_date = datetime.strptime(translated_date, "%A %d %B %Y").date()  # Get only the date

        # Define the event for the pay date as an all-day event
        pay_event_body = {
            'start': {'date': pay_date.isoformat(), 'timeZone': 'Europe/Amsterdam'},
            'end': {'date': (pay_date + timedelta(days=1)).isoformat(), 'timeZone': 'Europe/Amsterdam'},
            'summary': 'Appie Stacks 💰',
            'description': paydate['description'],
            'colorId': 5,  # Optional color ID for distinguishing pay dates
            'status': 'confirmed',
            'visibility': 'private'
        }

        # Insert the event for each pay date
        try:
            service.events().insert(
                calendarId=calendar_id,
                sendNotifications=True,
                sendUpdates='none',
                body=pay_event_body
            ).execute()
            print(f"Added pay date: {paydate['date']} - {paydate['description']}")
        except Exception as e:
            print(f"Failed to add pay date {paydate['date']}: {e}")


def login_navigate(driver):
    """Login and navigate towards Go! MW"""
    driver.get('https://euidp.aholddelhaize.com/pkmslogin.form')

    # Find the login form and fill it in
    driver.find_element(By.ID, 'uid').send_keys(creds.username)
    driver.find_element(By.ID, 'password').send_keys(creds.password)
    driver.find_element(By.CLASS_NAME, 'submitButton').click()

    # After logging in, navigate to the required page
    driver.get('https://sam.ahold.com/wrkbrn_jct/etm/etmMenu.jsp?locale=nl_NL')
    driver.find_element(By.XPATH, "//span[text()='Start']").click()


def scrape_data(driver):
    """Scrape the current month's shifts and return them in a list."""
    months = ['Januari', 'Februari', 'Maart', 'April', 'Mei', 'Juni', 'Juli',
              'Augustus', 'September', 'Oktober', 'November', 'December']
    month = driver.find_element(By.CLASS_NAME, 'calMonthTitle').text
    month = months.index(month) + 1
    year = int(driver.find_element(By.CLASS_NAME, 'calYearTitle').text)

    # Retrieve all shifts
    td_tags = driver.find_elements(By.TAG_NAME, 'td')
    past_shifts = [x for x in driver.find_elements(By.CLASS_NAME, 'calendarCellRegularPast') if x in td_tags]
    current_shifts = [x for x in driver.find_elements(By.CLASS_NAME, 'calendarCellRegularCurrent') if x in td_tags]
    future_shifts = [x for x in driver.find_elements(By.CLASS_NAME, 'calendarCellRegularFuture') if x in td_tags]

    all_shifts = [x.text.split('\n')[0:3] for x in (past_shifts + current_shifts + future_shifts)]

    # Adjust times if DST is not active
    hour_adjustment = -1 if time.localtime().tm_isdst != 1 else -2
    final_shifts = []

    for shift in all_shifts:
        if len(shift) == 1 or shift[1] == ' *':
            continue
        shift_date = int(shift[0])
        start_time, end_time = shift[1].replace('(', '').replace(')', '').split(' - ')
        start_hour, start_minute = map(int, start_time.split(':'))
        end_hour, end_minute = map(int, end_time.split(':'))

        shift_start = convert_to_RFC_datetime(year, month, shift_date, start_hour + hour_adjustment, start_minute)
        shift_end = convert_to_RFC_datetime(year, month, shift_date, end_hour + hour_adjustment, end_minute)

        final_shifts.append([shift_date, [shift_start, shift_end], shift[2] if len(shift) > 2 else ""])

    return final_shifts


def create_calendar(service):
    """Create calendar if it does not already exist."""
    request_body = {'summary': 'AH Werkrooster'}
    calendar_items = service.calendarList().list().execute().get('items')
    calendar_list = [calendar.get('summary') for calendar in calendar_items]

    if request_body['summary'] not in calendar_list:
        service.calendars().insert(body=request_body).execute()


def update_calendar(service, shifts):
    """Update calendar and insert the shifts."""
    calendar_id = get_calendar_id(service, 'AH Werkrooster')

    for shift in shifts:
        try:
            event_request_body = {
                'start': {'dateTime': shift[1][0], 'timeZone': 'Europe/Amsterdam'},
                'end': {'dateTime': shift[1][1], 'timeZone': 'Europe/Amsterdam'},
                'summary': 'AH Werk',
                'description': shift[2],
                'colorId': 7,
                'status': 'confirmed',
                'visibility': 'private'
            }
            service.events().insert(
                calendarId=calendar_id,
                sendNotifications=True,
                sendUpdates='none',
                body=event_request_body
            ).execute()
        except Exception as e:
            print(f"Error updating event: {e}")


def clear_calendar(service):
    """Clear all events from the calendar."""
    calendar_id = get_calendar_id(service, 'AH Werkrooster')
    page_token = None

    while True:
        events = service.events().list(calendarId=calendar_id, pageToken=page_token).execute()
        for event in events['items']:
            service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()
        page_token = events.get('nextPageToken')
        if not page_token:
            break


def get_calendar_id(service, title):
    """Retrieve the calendar ID by title."""
    calendar_items = service.calendarList().list().execute().get('items')
    return next(calendar['id'] for calendar in calendar_items if calendar['summary'] == title)


def navigate_next_month(driver):
    """Navigate to the next month and scrape data."""
    next_button_xpath = '/html/body/form/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr/td[2]/span'
    driver.find_element(By.XPATH, next_button_xpath).click()


def run():
    """Main function to run the process at scheduled times."""
    global service

    # Initialize Google Calendar API service
    CLIENT_SECRET_FILE = '/home/pira/Documents/Personal/appie-api/Client_Secret.json'
    API_NAME = 'calendar'
    API_VERSION = 'v3'
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

    # Create calendar if it doesn't exist
    create_calendar(service)

    # Start WebDriver
    chrome_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=chrome_service)

    try:
        # Log in and scrape shifts for current and next month
        login_navigate(driver)
        current_month_shifts = scrape_data(driver)
        navigate_next_month(driver)
        next_month_shifts = scrape_data(driver)

        # Clear and update the calendar with scraped shifts
        clear_calendar(service)
        update_calendar(service, current_month_shifts)
        update_calendar(service, next_month_shifts)
        add_paydates_to_calendar(service)
    finally:
        driver.quit()


if __name__ == '__main__':
    # Run the script once
    run()

    # # Schedule the job to run periodically
    # schedule.every().day.at("01:00").do(run)

    # while True:
    #     try:
    #         schedule.run_pending()
    #         time.sleep(1)
    #     except Exception as e:
    #         print(f"Scheduling failed: {e}")
