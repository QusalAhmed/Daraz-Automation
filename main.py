import json
import logging
import os
import re
import sqlite3
import threading
import time
import requests
import telebot
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys

# Configure logging settings
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# setting database
conn = sqlite3.connect('shop_data.db')
cursor = conn.cursor()
auto_reply_db = conn.cursor()
process_db = conn.cursor()

# Setting bot data
essential_cursor = conn.cursor()
bot_token = essential_cursor.execute(
    'SELECT value FROM essentials WHERE name = ?', ('bot_token',)).fetchone()[0]
# bot_token = '5618872665:AAED7ikwYNQxFfZzWwR6B8-NVB3LKb5P-SA'
bot = telebot.TeleBot(bot_token, parse_mode='Markdown')


def process_time(process_name):
    process_db.execute("SELECT execution_time FROM process_time WHERE name = ? AND shop_name = ?",
                       (process_name, database_shop_name))
    time_difference = (datetime.strptime(time.strftime("%Y %m %d-%H %M %S"), '%Y %m %d-%H %M %S') -
                       datetime.strptime(process_db.fetchone()[0], '%Y %m %d-%H %M %S'))
    if time_difference < timedelta(hours=5):
        return False
    else:
        return True


def export_cookies():
    new_cookie = json.dumps(driver.get_cookies())
    cursor.execute('UPDATE login_credential SET cookie = ? WHERE id = ?', (new_cookie, 1))
    conn.commit()


def login():
    driver.delete_all_cookies()
    load_page('https://sellercenter.daraz.com.bd/v2/seller/login')
    (wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, ".accountContent [type='text']"))).
     send_keys(email))
    driver.find_element(By.CSS_SELECTOR, ".accountContent [type='password']").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, ".loginButtonStyle").click()
    try:
        wait.until(ec.url_contains('https://sellercenter.daraz.com.bd/v2/home'))
    except Exception as login_error:
        print(login_error)
        login()
    # print(f"Response Code: {requests.head(driver.current_url).status_code}")
    new_cookie = json.dumps(driver.get_cookies())
    cursor.execute('UPDATE login_credential SET cookie = ? WHERE id = ?', (new_cookie, order))
    conn.commit()
    logging.info('Login Successful')


def send_message(message_text, notify=False):
    # telegram_api_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    #
    # try:
    #     response = requests.post(telegram_api_url, json={'chat_id': chat_id, 'text': message_text})
    #     print(response.text)
    # except Exception as send_message_error:
    #     print(send_message_error)

    bot.send_message('1747349969', message_text)
    if database_shop_name == 'Unique Live shopping':
        return True

    chat_id = '1783177827'  # -1001969295732
    bot.send_message(chat_id, message_text, disable_notification=notify)


def load_cookies(cookie_file):
    driver.delete_all_cookies()
    load_page('https://sellercenter.daraz.com.bd/apps/seller/login')
    cookies = json.loads(cookie_file)
    for cookie_data in cookies:
        driver.add_cookie(cookie_data)
    logging.info('Cookies loaded')
    login_status()


def simplified_text(input_string):
    # Define a regular expression pattern to match special characters and spaces
    pattern = r'[^\w\s\u0980-\u09FF[\]]+'

    # Use re.sub to remove special characters while preserving Bangla text
    cleaned_string = re.sub(pattern, '', input_string).strip()
    return cleaned_string.lower()


def to_md(text):
    return re.sub(r'([\[*_])', r'\\\1', text)


def check_message_status():
    logging.info('Checking message status')
    # if 'https://sellercenter.daraz.com.bd/v2/chat/window' not in driver.current_url:
    #     load_page('https://sellercenter.daraz.com.bd/v2/chat/window')
    load_page('https://sellercenter.daraz.com.bd/v2/chat/window')
    # total_msg = driver.find_element(By.CSS_SELECTOR, '[class^="SessionFilterOwnerTypeButton"]').text
    try:
        total_msg = wait.until(
            ec.presence_of_element_located((By.CSS_SELECTOR, '[class^="SessionFilterOwnerTypeButton"]'))).text
        if re.sub(r'\D', '', total_msg) == '0':
            driver.refresh()
    except TimeoutException:
        driver.refresh()
    time.sleep(1)
    try:
        wait.until(ec.presence_of_element_located((By.XPATH, "//span[contains(text(),'Unreplied')]"))).click()
        message_elements = driver.find_elements(By.CSS_SELECTOR, '[class^="SessionListItem"]')
    except NoSuchElementException:
        return True

    shop_name = driver.find_element(By.CLASS_NAME, 'im-page-header-switch-nickname').text
    for message_element in message_elements:
        msg_time = message_element.find_element(By.CSS_SELECTOR, '[class^="SessionDate"]').text
        # msg_title = message_element.find_element(By.CSS_SELECTOR, '[class^="SessionTitle"]').text
        message_element.find_element(By.CSS_SELECTOR, '[class^="SessionTitle"]').click()
        msg_title = message_scraping()
        if msg_title is None:
            continue
        msg_telegram = re.sub(r'([\[*_])', r'\\\1', msg_title)
        customer_msg = simplified_text(msg_title)
        sender_name = message_element.find_element(By.CSS_SELECTOR, '[class^="SessionTarget"]').text
        # try:
        #     msg_count = int(message_element.find_element(By.CSS_SELECTOR, '[class^="SessionBadge"]').text)
        # except NoSuchElementException:
        #     msg_count = 2
        auto_reply_db.execute("SELECT reply FROM auto_reply WHERE message = ?", (customer_msg,))
        auto_reply = auto_reply_db.fetchall()
        auto_reply_db.execute(
            'SELECT reply FROM external_reply WHERE query = ? AND shop_name = ? AND customer_name = ?',
            (customer_msg, shop_name, sender_name))
        external_reply = auto_reply_db.fetchall()
        if auto_reply:
            input_message(auto_reply)
            send_message('{} ♯{} ➤{}\n➥ {}'.format(
                shop_name, msg_time, msg_telegram, auto_reply[0][0], to_md(sender_name)), True)
            # bot.send_message(chat_id, '{} ♯{} ➤{}\n➥ {}'. format(shop_name, msg_time, msg_title,
            # auto_reply[0]), disable_notification=True)
        elif external_reply:
            input_message(external_reply)
            for single_reply in external_reply:
                send_message('{} ♯{} ➤{}\n╰┈➤ {}'.
                             format(shop_name, msg_time, msg_telegram, to_md(single_reply[0])), True)
            # bot.send_message(chat_id, '{} ♯{} ➤{}\n╰┈➤ {}'.
            #                  format(shop_name, msg_time, msg_title, external_reply[0]),
            #                  disable_notification=True)
            auto_reply_db.execute('DELETE FROM external_reply WHERE query = ? AND shop_name = ?',
                                  (customer_msg, shop_name))
            conn.commit()
        else:
            # message_element.find_element(By.CSS_SELECTOR, '[class^="SessionTitle"]').click()
            # wait.until(ec.presence_of_element_located(
            #     (By.CSS_SELECTOR, '[class^="scrollbar-styled MessageList"] .messageItem')))
            # time.sleep(2)
            image_name = shop_name + '-' + simplified_text(sender_name)
            driver.save_screenshot('Message Screenshot/' + image_name + '.png')
            try:
                if database_shop_name != 'Unique Live shopping':
                    bot.send_photo('1783177827', open('Message Screenshot/' + image_name + '.png', 'rb'))
                send_message('*{}* ♯{} ➤{}\n࿐{}'.
                             format(shop_name, msg_time, msg_telegram, to_md(sender_name)))
            except Exception as msg_sending_error:
                print(msg_sending_error)
            os.remove('Message Screenshot/' + image_name + '.png')
    cursor.execute('UPDATE login_credential SET remark = ? WHERE id = ?',
                   (time.strftime("%Y-%m-%d %H-%M-%S"), order))
    conn.commit()
    logging.info('Message status checked')


def home_inspection():
    if not process_time('home_inspection'):
        return True
    load_page('https://sellercenter.daraz.com.bd/v2/home')
    try:
        wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, '.learMoreButtonStyle'))).click()
        seller_pick_quota = driver.find_element(By.XPATH, "//div[@class='keyMetricsSeeMoreContent']/div["
                                                          "7]/div[2]/div[2]").text
        out_of_stock = (driver.find_element(By.XPATH, "//div[contains(text(),'Out Of Stock')]/..").
                        find_element(By.CSS_SELECTOR, ":nth-child(2)").text)
        if out_of_stock != '0':
            send_message('Out of Stock ↺ *{}*'.format(database_shop_name))
        if int(seller_pick_quota.split('/')[0]) != int(seller_pick_quota.split('/')[1]):
            send_message('Fix Seller Pick Quota ↺ *{}*'.format(database_shop_name))

        # Campaign
        while True:
            try:
                driver.find_element(By.CSS_SELECTOR, '.campaignEventsContent')
                break
            except NoSuchElementException:
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
        campaigns = driver.find_elements(By.CSS_SELECTOR,
                                         '.campaignEventsContent .singleCampaignEventContent')
        for campaign in campaigns:
            time_elements = campaign.find_elements(
                By.CSS_SELECTOR, '.singleCampaignEventBackgroundContent')
            campaign_title = campaign.find_element(By.CSS_SELECTOR, '.singleCampaignEventTitleStyle').text
            campaign_day = int(time_elements[0].text)
            campaign_hour = int(time_elements[1].text)
            if campaign_day == 0 and campaign_hour <= 12:
                campaign_cursor = conn.cursor()
                campaign_cursor.execute('SELECT * FROM campaign_alart WHERE shop_name = ? AND title = ?',
                                        (database_shop_name, campaign_title)).fetchone()
                send_message('Join Campaign 彡*{}* 🪐{}Hour(s) left\n{}'.
                             format(database_shop_name, campaign_hour, campaign_title))
    except NoSuchElementException:
        driver.refresh()
        home_inspection()

    process_db.execute("UPDATE process_time SET execution_time = ? WHERE (shop_name, name) = (?, ?)",
                       (time.strftime("%Y %m %d-%H %M %S"), database_shop_name, 'home_inspection'))
    conn.commit()


def message_scraping():  # inside message block
    message_brief = ''
    message_summary = ''
    try:
        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, '.user-type-1')))
    except TimeoutException:
        check_message_status()
    msg_window = wait.until(
        ec.presence_of_element_located((By.CSS_SELECTOR, '[class^="scrollbar-styled MessageList"]')))
    for msg_block in msg_window.find_elements(By.CSS_SELECTOR, '[class^="messageRow"]')[::-1]:
        msg_block_class = msg_block.get_attribute('class')
        if 'user-type-2' in msg_block_class:
            if message_summary == '':
                return None
            if 'row-card-image' in msg_block_class:
                driver.execute_script("arguments[0].remove();", msg_block)
            break
        elif 'row-card-text' in msg_block_class:
            message_summary += '\n' + msg_block.text
            message_brief = msg_block.text + '➛' + message_brief
        elif 'row-card-order' in msg_block_class:
            message_summary += ('\n' + msg_block.find_element(By.CSS_SELECTOR, '.card-header').text +
                                '\n Product: ' + msg_block.find_element(By.CSS_SELECTOR, '.text-info').text)
        elif 'row-card-system' in msg_block_class:
            pass
        elif 'row-card-product' in msg_block_class:
            product_details = msg_block.find_element(By.CSS_SELECTOR, '.lzd-pro-desc').text
            message_summary += '\nProduct: ' + product_details

    last_element = msg_window.find_elements(By.CSS_SELECTOR, '[class^="messageRow"]')[-1]
    driver.execute_script("arguments[0].scrollIntoView();", last_element)
    return re.sub(r'➛$', '', message_brief).strip()


def input_message(auto_reply):
    # message_element.find_element(By.CSS_SELECTOR, '[class^="SessionTitle"]').click()
    for single_reply in auto_reply:
        driver.find_element(By.CSS_SELECTOR, 'textarea').send_keys('\n' + single_reply[0])
    sent_button = driver.find_element(By.CSS_SELECTOR, '[class^="MessageInputBox"] button')
    sent_button.click()
    wait.until_not(ec.element_to_be_clickable(sent_button))


def order_limit():
    if not process_time('order_limit'):
        return True
    load_page('https://sellercenter.daraz.com.bd/order/query?tab=pending')
    try:
        if (wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'table td .next-table-empty')))
                .text == 'No Data'):
            return True
        order_limit_status = driver.find_element(By.CSS_SELECTOR, '.notices-container').text
    except NoSuchElementException:
        order_limit_status = False
    if ("Please process existing orders in order to continue to receive more orders." in order_limit_status
            and order_limit_status != ''):
        send_message(database_shop_name + ': ' + order_limit_status)
    rts()


def rts():
    try:
        order_no_element = driver.find_element(By.XPATH, "//span[contains(text(),'Pending')]")
        order_no = re.sub(r'\D', '', order_no_element.text)
        if order_no == '':
            return True
        elif int(order_no) <= 10:
            raise TimeoutException
        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, '.next-pagination')))
        mouse.move_to_element(
            driver.find_element(By.CSS_SELECTOR, '.orders-footer .next-icon-arrow-down')).perform()
        driver.find_element(By.CSS_SELECTOR, '.next-menu-content :nth-child(4)').click()
    except TimeoutException:
        pass

    pending_orders = driver.find_elements(By.CSS_SELECTOR, '.next-table-row')
    for pending_order in pending_orders[::-1]:
        pending_since = pending_order.find_element(By.CSS_SELECTOR, '.pendingSince').text
        # pending_since = "24 hours"
        if 'less than an hour' in pending_since:
            continue
        elif "Day" in pending_since or int(pending_since.split(' ')[0]) >= 15:
            WebDriverWait(pending_order, 10).until(
                ec.element_to_be_clickable((By.CSS_SELECTOR, '.next-table-row .next-checkbox'))).click()
    print('Selection Completed')
    if not (wait.until(ec.presence_of_element_located((By.XPATH, "//button[text()='Set Status']")))
            .is_enabled()):
        return True
    # mouse.move_to_element(
    #     driver.find_element(By.XPATH, "//button[text()='Set Status']")).perform()
    mouse.move_to_element(
        wait.until(ec.element_to_be_clickable((By.XPATH, "//button[text()='Set Status']")))).perform()
    try:
        # header_rts = driver.find_element(By.CSS_SELECTOR, '.next-menu-content :nth-child(1)')
        header_rts = wait.until(
            ec.element_to_be_clickable((By.CSS_SELECTOR, '.next-menu-content :nth-child(1)')))
    except NoSuchElementException:
        return True
    if header_rts.text.lower() == 'Ready to Ship'.lower():
        header_rts.click()
        try:
            time.sleep(2)
            wait.until(ec.visibility_of_element_located((By.XPATH, "//button[text()='Save invoice ID']")))
            wait.until(ec.element_to_be_clickable((By.XPATH, "//button[text()='Save invoice ID']"))).click()
        except TimeoutException:
            pass
        try:
            wait.until(
                ec.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Ready to ship')]"))).click()
            time.sleep(2)
        except TimeoutException:
            return True
        try:
            wait.until(ec.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Close')]"))).click()
        except TimeoutException:
            pass
    print('RTS completed')
    process_db.execute("UPDATE process_time SET execution_time = ? WHERE (shop_name, name) = (?, ?)",
                       (time.strftime("%Y %m %d-%H %M %S"), database_shop_name, 'order_limit'))
    conn.commit()


def move_click(move_element, click_element):
    mouse.move_to_element(driver.find_element(move_element)).perform()
    driver.find_element(click_element).click()


def load_page(page_url):
    try:
        driver.get(page_url)
    except TimeoutException:
        if page_url not in driver.current_url:
            load_page(page_url)


def question():
    logging.info('Checking question status')
    load_page('https://sellercenter.daraz.com.bd/msg/index')
    try:
        # question_element = driver.find_element(By.XPATH, "//div[contains(text(),'Customer Question')]").text
        question_element = wait.until(
            ec.presence_of_element_located((By.XPATH, "//div[contains(text(),'Customer Question')]"))).text
        # Get the number of question
        question_count = int(question_element.split('(')[1].split(')')[0])
        if question_count > 0:
            send_message('{} has {} question(s)'.format(database_shop_name, question_count))
    except NoSuchElementException:
        driver.refresh()
        question()
    except TimeoutException:
        driver.refresh()
        question()
    except IndexError:
        pass


def set_browser():
    try:
        wait_for_connection()
        browser_driver = webdriver.Chrome(service=service, options=options)
        browser_driver.implicitly_wait(2)
        # browser_driver.maximize_window()
        browser_driver.set_page_load_timeout(20)
        db_mouse = webdriver.ActionChains(browser_driver)
        driver_wait = WebDriverWait(browser_driver, 10)
        return browser_driver, driver_wait, db_mouse
    except Exception as browser_error:
        print(browser_error)
        set_browser()


def login_status():
    try:
        load_page('https://sellercenter.daraz.com.bd/v2/chat/window')
    except TimeoutException:
        pass
    if 'chat/window' not in driver.current_url:
        logging.error('Login Failed via cookies')
        login()


def window_handler():
    driver.execute_script("window.open('', '_blank');")


def wait_for_connection():
    while True:
        try:
            conn_request = requests.get('https://sellercenter.daraz.com.bd')
            if conn_request.status_code == 200:
                break
        except Exception as connection_error:
            print(connection_error)
            time.sleep(30)


# Function to handle incoming messages
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hi, I am online")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    message_text = message.text
    replied_message_text = message.reply_to_message.text
    if not replied_message_text:
        replied_message_text = message.reply_to_message.caption

    # Check if the message is a reply to another message
    if message.reply_to_message:
        # Store replied messages in the database
        store_replied_message(chat_id, message_text, replied_message_text)
    else:
        # Echo normal replies and store them in the database
        # store_replied_message(user_id, chat_id, message_id, message_text)
        echo_message(chat_id, message_text)


# Function to store replied messages in the database
def store_replied_message(chat_id, message_text, replied_message_text):
    # Create database connection
    external_reply_db = sqlite3.connect('shop_data.db')
    external_reply_cursor = external_reply_db.cursor()

    try:
        shop_name = replied_message_text.split('♯')[0].strip()
        query = replied_message_text.split('➤')[1].split('࿐')[0].strip()
        customer_name = replied_message_text.split('࿐')[1].strip()
    except IndexError:
        bot.send_message(chat_id, "_Can't process your reply_࿐")
        return True
    external_reply_cursor.execute(
        'INSERT INTO external_reply (query, reply, shop_name, customer_name) VALUES (?, ?, ?, ?)',
        (simplified_text(query), message_text, shop_name, customer_name))
    external_reply_db.commit()


# Function to echo normal replies
def echo_message(chat_id, message_text):
    # Your custom logic for echoing messages here
    # You can modify this part to perform specific actions
    # For now, we simply echo the message back to the user
    bot.send_message(chat_id, message_text)


# Function to periodically check for messages (e.g., every 10 seconds)
def check_for_messages():
    while True:
        try:
            bot.polling()
        except Exception as e:
            print(f'Error: {e}')
            continue


# Handling external reply ended

# service = Service(executable_path='driver/chromedriver.exe')
service = Service(executable_path='/usr/bin/chromedriver')
options = webdriver.ChromeOptions()
options.page_load_strategy = 'eager'
options.add_argument('--start-maximized')
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
options.add_argument('--disable-browser-side-navigation')
options.add_argument('--blink-settings=imagesEnabled=false')
options.add_argument("--window-size=1080, 1080")
options.add_argument("--zoom=1.5")

driver, wait, mouse = set_browser()
if __name__ == '__main__':
    # Start a separate thread to continuously check for messages
    message_thread = threading.Thread(target=check_for_messages)
    message_thread.start()
    print('Message Thread Started')
    while True:
        cursor.execute('SELECT * FROM login_credential')
        for row in cursor.fetchall():
            order, database_shop_name, email, password, cookie, remark = row
            print(f"ID: {order}\nShop Name: {database_shop_name}\nEmail: {email}\nPassword: {password}\n")
            try:
                load_cookies(cookie)
                check_message_status()
                home_inspection()
                order_limit()
                question()
            except Exception as error:
                print(error)
                driver.save_screenshot('Error Screenshot/' + database_shop_name +
                                       time.strftime(" %Y%m%d-%H%M%S") + '.png')
                try:
                    driver.quit()
                except Exception as quit_error:
                    print(quit_error)
                driver, wait, mouse = set_browser()
            conn.commit()
        print('Cycle Completed')
