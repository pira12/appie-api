import creds
from selenium import webdriver

# Start the chrome driver and go to login page.
driver = webdriver.Chrome('/home/pira/Documents/Personal/' +
                          'webdriver/chromedriver')
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

# Scrape all the info
month = driver.find_element_by_class_name('calMonthTitle').text
year = driver.find_element_by_class_name('calYearTitle').text

past_shifts = driver.find_elements_by_class_name('calendarCellRegularPast')
current_shifts = driver.find_elements_by_class_name('calendarCellRegularCurrent')
future_shifts = driver.find_elements_by_class_name('calendarCellRegularFuture')

for shift in past_shifts:
    date = ''
    time = ''

for shift in current_shifts:
    print(shift.text)

for shift in future_shifts:
    print(shift.text)