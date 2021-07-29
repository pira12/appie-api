import creds
from selenium import webdriver
from pprint import pprint
from Google import Create_Service, convert_to_RFC_datetime
from datetime import datetime, timedelta
from threading import Timer
import time
import schedule


def login_navigate():
    ''' Login and navigate towards Go! MW'''
    driver.get('https://euidp.aholddelhaize.com/pkmslogin.form')

    # Find the login form and fill it in
    username_textbox = driver.find_element_by_id('uid')
    username_textbox.send_keys(creds.username)

    password_textbox = driver.find_element_by_id('password')
    password_textbox.send_keys(creds.password)

    login_button = driver.find_element_by_class_name('submitButton')
    login_button.click()

    # After logging in navigate to GO! MW until you see the roster.
    driver.get('https://sam.ahold.com/wrkbrn_jct/etm/etmMenu.jsp?locale=nl_NL')
    start_button = driver.find_element_by_xpath("//span[text()='Start']")
    start_button.click()


def scrape_data():
    ''' Scrape the current month and return all the shifts in a list.'''
    # Scrape the moth and year
    months = ['Januari', 'Februari', 'Maart', 'April', 'Mei', 'Juni', 'Juli',
              'Augustus', 'September', 'Oktober', 'November', 'December']
    month = driver.find_element_by_class_name('calMonthTitle').text
    month = months.index(month) + 1
    year = int(driver.find_element_by_class_name('calYearTitle').text)

    # Scrape all the shifts
    td_tags = driver.find_elements_by_tag_name('td')
    past_shifts = [x for x in driver.find_elements_by_class_name(
                   'calendarCellRegularPast') if x in td_tags]
    current_shifts = [x for x in driver.find_elements_by_class_name(
                      'calendarCellRegularCurrent') if x in td_tags]
    future_shifts = [x for x in driver.find_elements_by_class_name(
                     'calendarCellRegularFuture') if x in td_tags]
    all_shifts = [x.text.split('\n')[0:3] for x in (past_shifts +
                                                    current_shifts +
                                                    future_shifts)]

    # Divide the times into start and ending time.
    hour_adjustment = -2
    final_shifts = []
    for shift in all_shifts:
        if len(shift) == 1:
            continue
        shift[1] = shift[1].replace('(', '')
        shift[1] = shift[1].replace(')', '')
        shift[1] = shift[1].split(' - ')
        shift[1][0] = convert_to_RFC_datetime(year, month, int(shift[0]),
                                              int(shift[1][0].split(':')[0]) +
                                              hour_adjustment,
                                              int(shift[1][0].split(':')[1]))
        shift[1][1] = convert_to_RFC_datetime(year, month, int(shift[0]),
                                              int(shift[1][1].split(':')[0]) +
                                              hour_adjustment,
                                              int(shift[1][1].split(':')[1]))
        shift[1] = shift[1:2][0]
        final_shifts.append(shift)

    return final_shifts


def create_calendar():
    ''' Creates and inserts a calendar if it does not alreaedy exist.'''
    request_body = {
        'summary': 'AH Werkrooster'
    }

    calendar_items = service.calendarList().list().execute().get('items')
    calendar_list = [calendar.get('summary') for calendar in calendar_items]

    if request_body.get('summary') not in calendar_list:
        service.calendars().insert(body=request_body).execute()


def update_calendar(shifts):
    ''' Update the calender and insert the shifts.'''
    my_calender_id = get_calendar_id('AH Werkrooster')

    # Insert shift as a event.
    for shift in shifts:
        event_request_body = {
            'start': {
                'dateTime': shift[1][0],
                'timeZone': 'Europe/Amsterdam'
            },
            'end': {
                'dateTime': shift[1][1],
                'timeZone': 'Europe/Amsterdam'
            },
            'summary': 'AH Werk',
            'description': shift[2],
            'colorId': 7,
            'status': 'confirmed',
            'visibility': 'private'
        }
        send_notification = True
        send_updates = 'none'

        service.events().insert(calendarId=my_calender_id,
                                sendNotifications=send_notification,
                                sendUpdates=send_updates,
                                body=event_request_body).execute()


def clear_calendar():
    ''' Clear everything on the calendar '''
    my_calender_id = get_calendar_id('AH Werkrooster')

    events = service.events().list(
                                   calendarId=my_calender_id
                                   ).execute().get('items')

    for event in events:
        service.events().delete(calendarId=my_calender_id,
                                eventId=event.get('id')).execute()


def get_calendar_id(title):
    ''' Get the calendat id, which is connected with the title'''
    calendar_items = service.calendarList().list().execute().get('items')
    my_calender = next(filter(lambda x: title in x['summary'], calendar_items))
    my_calender_id = my_calender.get('id')
    return my_calender_id


def navigate_next_month():
    ''' Navigates to the next moth and scrapes the info. '''
    next_button = driver.find_element_by_xpath('/html/body/form/table/tbody/' +
                                               'tr[2]/td/table/tbody/tr/td[2]/'
                                               + 'table/tbody/tr/td[2]/span')
    next_button.click()


if __name__ == '__main__':
    # Connecting the google calendar API.
    CLIENT_SECRET_FILE = 'Client_Secret.json'
    API_NAME = 'calendar'
    API_VERSION = 'v3'
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

    # Creates calendar if needed.
    create_calendar()

    def run():
        ''' The process which gets run everyday at 01:00. '''
        # Start the chrome driver.
        global driver
        # Fill in the path to chromedriver.
        driver = webdriver.Chrome()
        # Navigate and scrape current and next month.
        login_navigate()
        current_month_shifts = scrape_data()
        navigate_next_month()
        next_month_shifts = scrape_data()
        driver.close()
        # Clean the calender and update the shifts.
        clear_calendar()
        update_calendar(current_month_shifts)
        update_calendar(next_month_shifts)

    # Refresh the workcalender every 20 minutes.
    waiting_time = 60 * 20
    schedule.every(waiting_time).seconds.do(run)

    while 1:
        try:
            schedule.run_pending()
            time.sleep(1)
        except:
            driver.close()
            print("Failed")
