# import json
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support import expected_conditions as ec
# from selenium.webdriver.support.wait import WebDriverWait
# from selenium.common.exceptions import NoSuchElementException
# import requests
# import sqlite3
# import datetime
#
# # setting database
# conn = sqlite3.connect('shop_data.db')
# cursor = conn.cursor()
#
#
# def export_cookies():
#     new_cookie = json.dumps(driver.get_cookies())
#     cursor.execute('UPDATE login_credential SET cookie = ? WHERE id = ?', (new_cookie, 1))
#     conn.commit()
#
#
# def login():
#     driver.delete_all_cookies()
#     load_page('https://sellercenter.daraz.com.bd/v2/seller/login')
#     (wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, ".accountContent [type='text']"))).
#      send_keys(email))
#     driver.find_element(By.CSS_SELECTOR, ".accountContent [type='password']").send_keys(password)
#     driver.find_element(By.CSS_SELECTOR, ".loginButtonStyle").click()
#     try:
#         wait.until(ec.url_contains('https://sellercenter.daraz.com.bd/v2/home'))
#     except Exception as login_error:
#         print(login_error)
#         login()
#     print(f"Response Code: {requests.head(driver.current_url).status_code}")
#     new_cookie = json.dumps(driver.get_cookies())
#     cursor.execute('UPDATE login_credential SET cookie = ? WHERE id = ?', (new_cookie, order))
#     conn.commit()
#
#
# def send_message(message_text):
#     bot_token = '5618872665:AAED7ikwYNQxFfZzWwR6B8-NVB3LKb5P-SA'
#     chat_id = '1783177827'
#     telegram_api_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
#
#     try:
#         response = requests.post(telegram_api_url, json={'chat_id': chat_id, 'text': message_text})
#         print(response.text)
#     except Exception as send_message_error:
#         print(send_message_error)
#
#
# def load_cookies(cookie_file):
#     load_page('https://sellercenter.daraz.com.bd/')
#     cookies = json.loads(cookie_file)
#     for cookie_data in cookies:
#         driver.add_cookie(cookie_data)
#     load_page('https://sellercenter.daraz.com.bd/')
#     if 'home' not in driver.current_url:
#         login()
#
#
# def check_message_status():
#     load_page('https://sellercenter.daraz.com.bd/v2/chat/window')
#     try:
#         wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, '.ant-checkbox'))).click()
#         message_status = driver.find_element(By.CSS_SELECTOR, '[class^="SessionBadge"]')
#     except NoSuchElementException:
#         message_status = False
#     if message_status:
#         shop_name = driver.find_element(By.CLASS_NAME, 'im-page-header-switch-nickname').text
#         msg_time = driver.find_element(By.CSS_SELECTOR, '[class^="SessionDate"]').text
#         msg_title = driver.find_element(By.CSS_SELECTOR, '[class^="SessionTitle"]').text
#         msg_count = int(driver.find_element(By.CSS_SELECTOR, '[class^="SessionBadge"]').text)
#         if (msg_title in ["[Product card]", "[Order card]", '[পণ্যের কার্ড]', '[অর্ডার কার্ড]'] and msg_count
#                 == 1):
#             driver.find_element(By.CSS_SELECTOR, '[class^="SessionTitle"]').click()
#             driver.find_element(By.CSS_SELECTOR, 'textarea').send_keys('কিভাবে সহায়তা করতে পারি?')
#             sent_button = driver.find_element(By.CSS_SELECTOR, '[class^="MessageInputBox"] button')
#             sent_button.click()
#             wait.until_not(ec.element_to_be_clickable(sent_button))
#             send_message('{} at {}, {}\nReplied'.format(shop_name, msg_time, msg_title))
#         else:
#             send_message('{} at {}, {}'.format(shop_name, msg_time, msg_title))
#
#     driver.find_element(By.CSS_SELECTOR, "[class^='StationLogo']").click()
#     try:
#         wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, '.learMoreButtonStyle'))).click()
#         seller_pick_quota = driver.find_element(By.XPATH, "//div[@class='keyMetricsSeeMoreContent']/div["
#                                                           "7]/div[2]/div[2]").text
#         if int(seller_pick_quota.split('/')[0]) != int(seller_pick_quota.split('/')[1]):
#             if database_shop_name != 'Unique Live shopping':
#                 send_message('Fix Seller Pick Quota to {}'.format(database_shop_name))
#     except NoSuchElementException:
#         pass
#
#
# def order_limit():
#     load_page('https://sellercenter.daraz.com.bd/order/query?tab=pending')
#     try:
#         order_limit_status = driver.find_element(By.CSS_SELECTOR, '.notices-container').text
#     except NoSuchElementException:
#         order_limit_status = False
#     if ("Please process existing orders in order to continue to receive more orders." in order_limit_status
#             and order_limit_status != ''):
#         send_message(order_limit_status)
#
#
# def load_page(page_url):
#     driver.get(page_url)
#     try:
#         wait.until(ec.url_contains(page_url))
#     except Exception as load_page_error:
#         print(load_page_error)
#         load_page(page_url)
#
#
# def question():
#     load_page('https://sellercenter.daraz.com.bd/msg/index')
#     question_element = driver.find_element(By.XPATH, "//div[contains(text(),'Customer Question')]").text
#     # Get the number of question
#     question_count = int(question_element.split('(')[1].split(')')[0])
#     if question_count > 0:
#         send_message('{} has {} question(s)'.format(database_shop_name, question_count))
#
#
# def set_browser():
#     browser_driver = webdriver.Chrome(service=service, options=options)
#     browser_driver.implicitly_wait(10)
#     browser_driver.maximize_window()
#     browser_wait = WebDriverWait(browser_driver, 10)
#     return browser_driver, browser_wait
#
#
# def login_status():
#     response = requests.get('https://sellercenter.daraz.com.bd/v2/chat/window')
#     data = response.json()
#     print(data['status'])
#
#
# service = Service(executable_path='driver\\chromedriver.exe')
# options = webdriver.ChromeOptions()
# # options.add_argument('--headless')
# # options.add_argument('--disable-gpu')
# # # options.add_argument('--no-sandbox')
# # options.add_argument('--disable-dev-shm-usage')
# # options.add_argument('--ignore-certificate-errors')
# # options.add_argument('--ignore-ssl-errors')
#
# # make driver for all the shops
# cursor.execute('SELECT * FROM login_credential')
# driver_array = []
# wait_array = []
# for row in cursor.fetchall():
#     driver, wait = set_browser()
#     driver_array.append(driver)
#     wait_array.append(wait)
#
# while True:
#     cursor.execute('SELECT * FROM login_credential')
#     for row in cursor.fetchall():
#         order, database_shop_name, email, password, cookie, remark = row
#         print(f"ID: {order}\nShop Name: {database_shop_name}\nEmail: {email}\nPassword: {password}\n")
#         driver = driver_array[order - 1]
#         wait = wait_array[order - 1]
#         try:
#             # login_status()
#             load_cookies(cookie)
#             check_message_status()
#             cursor.execute('UPDATE login_credential SET remark = ? WHERE id = ?',
#                            (datetime.datetime.now(), order))
#             order_limit()
#             question()
#         except Exception as error:
#             print(error)
#             driver.quit()
#             driver, wait = set_browser()
#             driver_array[order - 1] = driver
#             wait_array[order - 1] = wait
#         conn.commit()
