import creds
from selenium import webdriver

username = creds.username
password = creds.password

driver = webdriver.Chrome('/home/pira/Documents/Personal/webdriver/chromedriver')
driver.get('https://euidp.aholddelhaize.com/pkmslogin.form')

username_textbox = driver.find_element_by_id('uid')
username_textbox.send_keys(username)

password_textbox = driver.find_element_by_id('password')
password_textbox.send_keys(password)

login_button = driver.find_element_by_class_name('submitButton')
login_button.click()

driver.get('https://sam.ahold.com/wrkbrn_jct/etm/etmMenu.jsp?locale=nl_NL')

start_button = driver.find_element_by_xpath("//span[text()='Start']")
start_button.click()