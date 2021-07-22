import creds
from selenium import webdriver


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
    month = driver.find_element_by_class_name('calMonthTitle').text
    year = driver.find_element_by_class_name('calYearTitle').text

    # Scrape all the shifts
    td_tags = driver.find_elements_by_tag_name('td')
    past_shifts = [x for x in driver.find_elements_by_class_name('calendarCellRegularPast') if x in td_tags]
    current_shifts = [x for x in driver.find_elements_by_class_name('calendarCellRegularCurrent') if x in td_tags]
    future_shifts = [x for x in driver.find_elements_by_class_name('calendarCellRegularFuture') if x in td_tags]
    all_shifts = [x.text.split('\n')[0:3] for x in (past_shifts + current_shifts + future_shifts)]

    return all_shifts


if __name__ == '__main__':
    # Start the chrome driver.
    driver = webdriver.Chrome('/home/pira/Documents/Personal/' +
                            'webdriver/chromedriver')


    login_navigate()
    print(scrape_data())

    driver.close()