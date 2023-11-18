import inspect
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
from selenium.common.exceptions import (NoSuchElementException, StaleElementReferenceException,
                                        TimeoutException)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys

# Configure logging settings
logging.basicConfig(level=logging.INFO, filename='bot.log', filemode='w',
                    format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# setting database
conn = sqlite3.connect('shop_data.db', check_same_thread=False)
cursor = conn.cursor()
# cursor.execute("UPDATE process_time SET execution_time = ? WHERE name = ?",
#                ('2022-10-07 21:31:06', 'check_message_status'))
# conn.commit()

# Global variable
extra_process = True
triumph = None

# Setting bot data
essential_cursor = conn.cursor()
bot_token = essential_cursor.execute(
    'SELECT value FROM essentials WHERE name = ?', ('bot_token',)).fetchone()[0]
bot = telebot.TeleBot(bot_token, parse_mode='Markdown')


def instance_data(shop_name, ins_driver, ins_wait, ins_mouse):
    cursor.execute('SELECT * FROM login_credential WHERE shop_name = ?', (shop_name,))
    ins_order, ins_shop_name, ins_email, ins_password, ins_cookie, ins_remark = cursor.fetchone()
    ins_driver = ins_driver[ins_order - 1]
    ins_wait = ins_wait[ins_order - 1]
    ins_mouse = ins_mouse[ins_order - 1]
    return (ins_order, ins_shop_name, ins_email, ins_password, ins_cookie, ins_remark,
            ins_driver, ins_wait, ins_mouse)


def process_time(process_name, execution_period=180, shop_name='all'):
    if execution_period == 0:
        execution_period = 180
    cursor.execute('SELECT * FROM process_time WHERE (name, shop_name) = (?, ?)', (process_name, shop_name))
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO process_time (name, shop_name, execution_time) VALUES (?, ?, ?)',
                       (process_name, shop_name, time.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    cursor.execute('select * from process_time WHERE execution_time < ? AND (name, shop_name) = (?, ?)',
                   (datetime.now() - timedelta(minutes=execution_period), process_name, shop_name))
    if cursor.fetchone() is not None:
        return True
    else:
        return False


def between_time():
    current_time = datetime.now().time()
    start_time = datetime.strptime('03:00:00', '%H:%M:%S').time()
    end_time = datetime.strptime('10:00:00', '%H:%M:%S').time()
    if start_time <= current_time <= end_time:
        return True
    else:
        return False


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
    except TimeoutException:
        login()
        return True
    new_cookie = json.dumps(driver.get_cookies())
    cursor.execute('UPDATE login_credential SET cookie = ? WHERE id = ?', (new_cookie, order))
    conn.commit()
    print('Login Successful')
    load_page('https://sellercenter.daraz.com.bd/v2/chat/window')


def send_message(message_text, notify=False):
    chat_id = '1783177827'  # -1001969295732
    # chat_id_group = '-1001982474657'
    bot.send_message(chat_id, message_text, disable_notification=notify)
    # bot.send_message(chat_id_group, message_text, disable_notification=notify)


def load_cookies(cookie_file):
    driver.switch_to.window(driver.window_handles[1])
    load_page('https://sellercenter.daraz.com.bd/v2/home')
    if 'daraz.com.bd/v2/home' in driver.current_url:
        driver.switch_to.window(driver.window_handles[0])
        return True
    driver.switch_to.window(driver.window_handles[0])
    driver.delete_all_cookies()
    load_page('https://sellercenter.daraz.com.bd/apps/seller/login')
    cookies = json.loads(cookie_file)
    for cookie_data in cookies:
        driver.add_cookie(cookie_data)
    print('Cookies loaded')
    login_status()


def simplified_text(input_string):
    # Define a regular expression pattern to match special characters and spaces
    pattern = r'[^\w\s\➛\u0980-\u09FF[\]]+'
    cleaned_string = re.sub(pattern, '', input_string).strip()
    return cleaned_string.lower()


def to_md(text):
    return re.sub(r'([\[*_])', r'\\\1', text)


def send_image(shop_name, sender_name):
    image_name = shop_name + '-' + simplified_text(sender_name)
    driver.save_screenshot('Message Screenshot/' + image_name + '.png')
    try:
        bot.send_photo('1783177827', open('Message Screenshot/' + image_name + '.png', 'rb'))
    except Exception as msg_sending_error:
        print(msg_sending_error)
    os.remove('Message Screenshot/' + image_name + '.png')


def recheck(customer_msg, shop_name, sender_name, msg_time, reply):
    msg_telegram_re = simplified_text(message_scraping(reply))
    if customer_msg != msg_telegram_re:
        msg_telegram = re.sub(r'([\[*_])', r'\\\1', msg_telegram_re.replace(customer_msg, ''))
        if msg_telegram.startswith('➛'):
            msg_telegram = msg_telegram[1:]
        send_image(shop_name, sender_name)
        send_message('__✺Extra__ *{}* ♯{} ➤{}\n࿐{}'.
                     format(shop_name, msg_time, msg_telegram, to_md(sender_name)))


def check_message_status():
    global extra_process
    if extra_process and process_time('check_message_status', 60, database_shop_name):
        print('Setting up message status')
        driver.refresh()
        extra_process = False
        cursor.execute("UPDATE process_time SET execution_time = ? WHERE (shop_name, name) = (?, ?)",
                       (time.strftime("%Y-%m-%d %H:%M:%S"), database_shop_name, 'check_message_status'))
        conn.commit()
        try:
            wait.until_not(ec.presence_of_element_located((By.CSS_SELECTOR, '.chat-spin-dot-spin')))
            # wait.until(ec.presence_of_element_located((By.XPATH, "//span[contains(text(),'Unreplied')]")))
            # total_msg = wait.until(ec.presence_of_element_located(
            #     (By.CSS_SELECTOR, '[class^="SessionFilterOwnerTypeButton"]'))).text
            # if re.sub(r'\D', '', total_msg) == '0':
            #     raise TimeoutException
        except TimeoutException:
            driver.refresh()
            check_message_status()
            return True
    print('Checking message status')
    cursor.execute('SELECT value FROM essentials WHERE name = ?', ('debug',))
    if cursor.fetchone()[0] == '1':
        driver.save_screenshot('Debug/' + database_shop_name + '.png')
    try:
        wait.until(ec.presence_of_element_located((By.XPATH, "//span[contains(text(),'Unreplied')]")))
        unreplied_filter_class = driver.find_element(
            By.XPATH, "//span[contains(text(),'Unreplied')]").get_attribute('class')
        if 'SessionFilterTagActive' not in unreplied_filter_class:
            driver.find_element(By.XPATH, "//span[contains(text(),'Unreplied')]").click()
        if wait.until(ec.presence_of_element_located(
                (By.CSS_SELECTOR, '[class^="SessionList"]'))).text == 'No Data':
            cursor.execute('UPDATE login_credential SET remark = ? WHERE id = ?',
                           (time.strftime("%Y-%m-%d %H:%M:%S"), order))
            conn.commit()
            print('Message status checked')
            return True
        message_elements = driver.find_elements(By.CSS_SELECTOR, '[class^="SessionListItem"]')
    except NoSuchElementException:
        return False

    shop_name = driver.find_element(By.CLASS_NAME, 'im-page-header-switch-nickname').text
    for message_element in message_elements:
        msg_time = message_element.find_element(By.CSS_SELECTOR, '[class^="SessionDate"]').text
        message_element.find_element(By.CSS_SELECTOR, '[class^="SessionTitle"]').click()
        msg_title = message_scraping()
        if msg_title is None:
            continue
        msg_telegram = re.sub(r'([\[*_])', r'\\\1', msg_title)
        customer_msg = simplified_text(msg_title)
        sender_name = driver.find_element(By.CSS_SELECTOR, '[class^="UserNickname"]').text
        # try:
        #     sender_name = message_element.find_element(By.CSS_SELECTOR, '[class^="SessionTarget"]').text
        # except NoSuchElementException:
        #     return True
        auto_reply = []
        for message in customer_msg.split('➛'):
            cursor.execute("SELECT reply FROM auto_reply WHERE message = ?", (message,))
            stored_reply = cursor.fetchone()
            if stored_reply is None:
                auto_reply = []
                break
            auto_reply.append(stored_reply)
        cursor.execute(
            'SELECT reply FROM external_reply WHERE query = ? AND shop_name = ? AND customer_name = ?',
            (customer_msg, shop_name, sender_name))
        external_reply = cursor.fetchall()

        cursor.execute(
            'SELECT send_time FROM send_time WHERE (customer_name, query, shop_name) = (?, ?, ?)',
            (sender_name, customer_msg, shop_name))
        last_send_time = cursor.fetchone()
        if auto_reply:
            input_message(auto_reply)
            auto_reply_1d = []
            for reply in auto_reply:
                auto_reply_1d.append(reply[0])
            # send_message('{} ♯{} ➤{}\n➥ {}'.format(
            #     shop_name, msg_time, msg_telegram, '⌒'.join(auto_reply_1d), to_md(sender_name)), True)
            recheck(customer_msg, shop_name, sender_name, msg_time, auto_reply)
        elif external_reply:
            input_message(external_reply)
            for single_reply in external_reply:
                send_message('{} ♯{} ➤{}\n╰┈➤ {}'.
                             format(shop_name, msg_time, msg_telegram, to_md(single_reply[0])), True)
                cursor.execute('DELETE FROM external_reply WHERE (reply, shop_name, customer_name) = (?, ?, ?)',
                               (single_reply[0], shop_name, sender_name))
            cursor.execute('DELETE FROM send_time WHERE (customer_name, query, shop_name) = (?, ?, ?)',
                           (sender_name, customer_msg, shop_name))
            conn.commit()
            recheck(customer_msg, shop_name, sender_name, msg_time, external_reply)
        else:
            if last_send_time is not None:
                time_difference = (
                        datetime.strptime(time.strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S') -
                        datetime.strptime(last_send_time[0], '%Y-%m-%d %H:%M:%S'))
                if time_difference > timedelta(minutes=30):
                    send_image(shop_name, sender_name)
                    send_message('*{}* ♯{} ➤{}\n࿐{}'.
                                 format(shop_name, msg_time, msg_telegram, to_md(sender_name)))
                    cursor.execute('UPDATE send_time SET send_time = ? WHERE (customer_name, query, shop_name) = '
                                   '(?, ?, ?)',
                                   (time.strftime("%Y-%m-%d %H:%M:%S"), sender_name, customer_msg, shop_name))
            else:
                cursor.execute(
                    'INSERT INTO send_time (customer_name, query, shop_name, send_time) VALUES (?, ?, ?, ?)',
                    (sender_name, customer_msg, shop_name, time.strftime("%Y-%m-%d %H:%M:%S")))
                send_image(shop_name, sender_name)
                send_message('*{}* ♯{} ➤{}\n࿐{}'.format(shop_name, msg_time, msg_telegram, to_md(sender_name)))
            conn.commit()
    driver.refresh()
    cursor.execute('UPDATE login_credential SET remark = ? WHERE id = ?',
                   (time.strftime("%Y-%m-%d %H:%M:%S"), order))
    conn.commit()
    print('Message status checked')
    return True


def fix_reply():
    cursor.execute('SELECT * FROM reply_fix WHERE shop_name = ?', (database_shop_name,))
    for reply_to in cursor.fetchall():
        serial, reply, customer_name, shop_name, message_id = reply_to
        unreplied_filter_class = driver.find_element(
            By.XPATH, "//span[contains(text(),'Unreplied')]").get_attribute('class')
        if 'SessionFilterTagActive' in unreplied_filter_class:
            driver.find_element(By.XPATH, "//span[contains(text(),'Unreplied')]").click()
            time.sleep(1)
        driver.find_element(
            By.XPATH, '//div[@class="chat-spin-container"] //div[contains(text(),customer_name)]').click()
        set_message_interface()
        msg_window = wait.until(
            ec.presence_of_element_located((By.CSS_SELECTOR, '[class^="scrollbar-styled MessageList"]')))
        mouse.move_to_element(
            msg_window.find_elements(By.CSS_SELECTOR, '[class^="messageRow"]')[-1]).perform()
        if ('user-type-2' in msg_window.find_elements(By.CSS_SELECTOR, '[class^="messageRow"]')[-1].
                get_attribute('class')):
            input_message(((reply,),))
            send_message('*Fix Reply* 彡{} 🕊{}✸ ࿐{}'.format(shop_name, to_md(reply), customer_name), False)
            cursor.execute('DELETE FROM reply_fix WHERE serial = ?', (serial,))
            conn.commit()
        else:
            send_message('*☠Drop Fix Reply* 彡{} 🕊{}✸'.format(shop_name, to_md(reply), True))
            cursor.execute('DELETE FROM reply_fix WHERE serial = ?', (serial,))
            conn.commit()


def home_metrics(text):
    return (driver.find_element(By.XPATH, f"//div[contains(text(),'{text}')]/..").
            find_element(By.CSS_SELECTOR, ":nth-child(2)").text)


def to_float(text):
    try:
        return float(re.sub(r'[^\d.]', '', text))
    except ValueError:
        return 0


def campaign_alert():
    cursor.execute('SELECT * FROM campaign_alert')
    campaigns = cursor.fetchall()
    for campaign in campaigns:
        serial, campaign_name, shop_name, time_left, status = campaign
        time_difference = (datetime.strptime(time_left, '%Y-%m-%d %H:%M:%S') -
                           datetime.strptime(time.strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S'))
        hour_left = time_difference.seconds // 3600
        minute_left = (time_difference.seconds % 3600) // 60
        if time_difference > timedelta(minutes=0) and status == 'True':
            send_message('Join Campaign 彡*{}* 🪐{}Hour(s) {}Minute(s) left\n☪{}'.
                         format(shop_name, hour_left, minute_left, to_md(campaign_name)))
        elif time_difference <= timedelta(minutes=0):
            cursor.execute('DELETE FROM campaign_alert WHERE serial = ?', (serial,))
            conn.commit()
    cursor.execute("UPDATE process_time SET execution_time = ? WHERE name = ?",
                   (time.strftime("%Y-%m-%d %H:%M:%S"), 'campaign_alert'))
    conn.commit()


def home_inspection():
    print('Home Inspection Started')
    load_page('https://sellercenter.daraz.com.bd/v2/home')
    wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, '.learMoreButtonStyle'))).click()
    seller_pick_quota = driver.find_element(By.XPATH, "//div[@class='keyMetricsSeeMoreContent']/div["
                                                      "7]/div[2]/div[2]").text
    out_of_stock = (driver.find_element(By.XPATH, "//div[contains(text(),'Out Of Stock')]/..").
                    find_element(By.CSS_SELECTOR, ":nth-child(2)").text)
    review = int(driver.find_element(By.XPATH, "//div[contains(text(),'New Reviews')]/..").
                 find_element(By.CSS_SELECTOR, "span").text)
    if out_of_stock != '0':
        send_message('Out of Stock ↺ *{}*'.format(database_shop_name))
    if int(seller_pick_quota.split('/')[0]) != int(seller_pick_quota.split('/')[1]):
        send_message('Fix Seller Pick Quota ↺ *{}*'.format(database_shop_name))

    # DB
    scrap_element = {
        'Review': review,
        'Product Rating': to_float(home_metrics('Product Rating')),
        '%Orders Processed Within SLA': to_float(home_metrics('%Orders Processed Within SLA')),
    }
    for key, value in scrap_element.items():
        cursor.execute(
            'SELECT metrics_value FROM home_metrics WHERE (metrics_type, shop_name) = (?, ?)',
            (key, database_shop_name))
        home_metrics_db = cursor.fetchone()
        if home_metrics_db is None:
            cursor.execute(
                'INSERT INTO home_metrics (metrics_type, metrics_value, shop_name) VALUES (?, ?, ?)',
                (key, value, database_shop_name))
            conn.commit()
            continue
        if float(value) > float(home_metrics_db[0]):
            send_message('{}➶ {}*~*{} ⊂⊃ *{}*'.format(key, home_metrics_db[0], value, database_shop_name))
        elif float(value) < float(home_metrics_db[0]):
            send_message('{}➴ {}*~*{} ⊂⊃ *{}*'.format(key, home_metrics_db[0], value, database_shop_name))
        else:
            continue
        cursor.execute(
            'UPDATE home_metrics SET metrics_value = ? WHERE (metrics_type, shop_name) = (?, ?)',
            (value, key, database_shop_name))
        conn.commit()

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
        cursor.execute('SELECT status FROM campaign_alert WHERE name = ? AND shop_name = ?',
                       (campaign_title, database_shop_name))
        if cursor.fetchone() == ('False',):
            continue
        campaign_day = int(time_elements[0].text)
        campaign_hour = int(time_elements[1].text)
        if campaign_day == 0 and campaign_hour <= 12:
            send_message('Join Campaign 彡*{}* 🪐{}Hour(s) left\n☪{}'.
                         format(database_shop_name, campaign_hour, to_md(campaign_title)))
            cursor.execute(
                "UPDATE process_time SET execution_time = ? WHERE (shop_name, name) = (?, ?)",
                (datetime.strptime(time.strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S') -
                 timedelta(hours=2), database_shop_name, 'home_inspection'))
            conn.commit()
            return True
        if -1 < campaign_day < 0:
            send_message('Join Campaign 彡*{}* 🪐{}Hour(s) _late_\n☪{}'.
                         format(database_shop_name, 24 - campaign_hour, campaign_title))
            cursor.execute(
                "UPDATE process_time SET execution_time = ? WHERE (shop_name, name) = (?, ?)",
                (datetime.strptime(time.strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S') -
                 timedelta(hours=2), database_shop_name, 'home_inspection'))
            conn.commit()
            return True

    cursor.execute("UPDATE process_time SET execution_time = ? WHERE (shop_name, name) = (?, ?)",
                   (time.strftime("%Y-%m-%d %H:%M:%S"), database_shop_name, 'home_inspection'))
    conn.commit()
    print('Home Inspection Completed')


def set_message_interface():
    try:
        wait.until_not(
            ec.presence_of_all_elements_located((By.CSS_SELECTOR, '[class^="PanelMain"] .anticon-loading')))
        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, '.user-type-1')))
    except TimeoutException:
        cursor.execute("UPDATE process_time SET execution_time = ? WHERE name = ?",
                       ('2022-10-07 21:31:06', 'check_message_status'))
        conn.commit()
        check_message_status()
        return 'Repeat'


def message_scraping(ignore=()):  # inside message block
    message_brief = ''
    message_summary = ''
    if set_message_interface() == 'Repeat':
        return None
    msg_window = wait.until(
        ec.presence_of_element_located((By.CSS_SELECTOR, '[class^="scrollbar-styled MessageList"]')))
    mouse.move_to_element(msg_window.find_elements(By.CSS_SELECTOR, '[class^="messageRow"]')[-1]).perform()
    mouse.scroll_to_element(msg_window.find_elements(By.CSS_SELECTOR, '[class^="messageRow"]')[-1]).perform()
    for msg_block in msg_window.find_elements(By.CSS_SELECTOR, '[class^="messageRow"]')[::-1]:
        msg_block_class = msg_block.get_attribute('class')
        if 'user-type-2' in msg_block_class:
            if 'row-card-image' in msg_block_class:
                driver.execute_script("arguments[0].remove();", msg_block)
                continue
            # elif 'row-card-text' in msg_block_class:
            #     message_text = msg_block.find_element(By.CSS_SELECTOR, '.message-text-box').text
            #     if (message_text,) in ignore:
            #         ignore = tuple(x for x in ignore if x != message_text)
            #         continue
            if ignore != () and message_summary == '':
                continue
            if message_summary == '':
                return None
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
        elif 'row-card-image' in msg_block_class:
            time.sleep(1)
            mouse.send_keys_to_element(msg_window, Keys.PAGE_DOWN).perform()
            try:
                message_summary += ('\nImage: ' + msg_block.
                                    find_element(By.CSS_SELECTOR, 'img').get_attribute('src'))
            except Exception as image_error:
                print(image_error)
                message_summary += '\nImage: ' + msg_block.text
        else:
            message_summary += '\n' + msg_block.text

    return re.sub(r'➛$', '', message_brief).strip()


def input_message(auto_reply):
    for single_reply in auto_reply:
        driver.find_element(By.CSS_SELECTOR, 'textarea').send_keys('\n' + single_reply[0])
    sent_button = driver.find_element(By.CSS_SELECTOR, '[class^="MessageInputBox"] button')
    sent_button.click()
    wait.until_not(ec.element_to_be_clickable(sent_button))


def campaign_insertion(campaign_name, hour_left, min_left):
    cursor.execute('SELECT * FROM campaign_alert WHERE name = ? AND shop_name = ?',
                   (campaign_name, database_shop_name))
    if cursor.fetchone() is None:
        time_left = (datetime.strptime(time.strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S') +
                     timedelta(hours=hour_left, minutes=min_left))
        cursor.execute(
            'INSERT INTO campaign_alert (name, time_left, shop_name) VALUES (?, ?, ?)',
            (campaign_name, time_left, database_shop_name))
        conn.commit()


def campaign_overview_monitor():
    global extra_process
    global triumph
    if inspect.currentframe().f_back.f_code.co_name != inspect.currentframe().f_code.co_name:
        triumph = 0
    try:
        campaign_overview()
    except StaleElementReferenceException:
        driver.save_screenshot('Error Screenshot/' + 'Campaign-' + database_shop_name + '.png')
        wait_for_connection()
        if triumph <= 1:
            campaign_overview_monitor()
            triumph += 1
        else:
            print('Campaign Overview Maximum Times Failed')
            return False
        return True
    finally:
        extra_process = False


def campaign_overview():
    if 'https://sellercenter.daraz.com.bd/v2/campaign/portal' not in driver.current_url:
        load_page('https://sellercenter.daraz.com.bd/v2/campaign/portal', '.next-tabs-nav-scroll')
    load_page('https://sellercenter.daraz.com.bd/v2/campaign/portal', '.next-tabs-nav-scroll')
    print('Campaign Overview Started')
    for main_tab in driver.find_elements(
            By.CSS_SELECTOR, '#centerContent > :nth-child(1) > :nth-child(1) > :nth-child(3) li'):
        wait.until(ec.element_to_be_clickable(main_tab))
        main_tab.click()
        time.sleep(1)
        for sub_tab in driver.find_elements(
                By.CSS_SELECTOR, '#centerContent > :nth-child(1) > :nth-child(1) > :nth-child(4) li'):
            # if sub_tab.text == '':
            #     continue
            wait.until(ec.element_to_be_clickable(sub_tab))
            sub_tab.click()
            time.sleep(1)
            for type_tab in driver.find_elements(
                    By.CSS_SELECTOR, '#centerContent > :nth-child(1) > :nth-child(1) > :nth-child(5) li'):
                wait.until(ec.element_to_be_clickable(type_tab))
                type_tab.click()
                time.sleep(1)
                campaign_element = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'tbody tr')))
                if campaign_element.text == 'No Data' or campaign_element.text == '':
                    continue
                if type_tab.text == 'Special Invitation':
                    for campaign in wait.until(
                            ec.presence_of_all_elements_located((By.CSS_SELECTOR, 'tbody tr'))):
                        status = campaign.find_element(By.CSS_SELECTOR, 'td[name="status"]').text
                        if status == 'Pending' or status == 'Registration in Progress':
                            name = campaign.find_element(By.CSS_SELECTOR, 'td[name="name"]').text
                            end_date = (campaign.find_element(
                                By.CSS_SELECTOR, "td[name='registerEndTime']").text
                                        .split('GMT')[0].strip())
                            time_left = datetime.strptime(end_date, '%d %b %Y %H:%M') - datetime.now()
                            if time_left < timedelta(hours=18):
                                hour_left = time_left.seconds // 3600
                                minute_left = (time_left.seconds % 3600) // 60
                                # send_message('Join Campaign 彡*{}* 🪐{}Hour(s) {}Minute(s) left\n☪{}'.
                                #              format(database_shop_name, hour_left, minute_left, name))
                                campaign_insertion(name, hour_left, minute_left)
                elif type_tab.text == 'Available Campaign':
                    day_left = 99
                    hour_left = 0
                    minute_left = 0
                    for campaign in wait.until(
                            ec.presence_of_all_elements_located((By.CSS_SELECTOR, 'tbody tr'))):
                        name = campaign.find_element(By.CSS_SELECTOR, 'td[name="name"]').text
                        end_time = campaign.find_element(By.CSS_SELECTOR, ".count-down").text
                        for time_part in end_time.split(':'):
                            if time_part.endswith("d"):
                                day_left = int(time_part[:-1])
                            elif time_part.endswith("h"):
                                hour_left = int(time_part[:-1])
                            elif time_part.endswith("m"):
                                minute_left = int(time_part[:-1])
                        if day_left == 0 and hour_left <= 18:
                            # send_message('Join Campaign 彡*{}* 🪐{}Hour(s) {}Minute(s) left\n☪{}'.
                            #              format(database_shop_name, hour_left, minute_left, name))
                            campaign_insertion(name, hour_left, minute_left)
                elif sub_tab.text == 'Flash Sale' and type_tab.text == 'Registered Campaign':
                    print('Flash Sale')
                    campaign = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'tbody tr')))
                    status = campaign.find_element(By.CSS_SELECTOR, 'td[name="status"]').text
                    if status == 'Offline':
                        break
                    (mouse.key_down(Keys.CONTROL).click(
                        campaign.find_element(By.CSS_SELECTOR, 'button')).key_up(Keys.CONTROL).perform())
                    driver.switch_to.window(driver.window_handles[2])
                    wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, '.next-tabs-bar')))
                    approved_text = wait.until(ec.presence_of_element_located(
                        (By.XPATH, "//div[contains(text(),'Approved')]"))).text
                    approved_product = int(approved_text.split('(')[1].split(')')[0])
                    pending_text = wait.until(ec.presence_of_element_located(
                        (By.XPATH, "//div[contains(text(),'Pending Allocation')]"))).text
                    pending_product = int(pending_text.split('(')[1].split(')')[0])
                    if approved_product > 0:
                        send_message('Flash Sale Approved ↺ *{}*'.format(database_shop_name))
                    elif pending_product > 0:
                        send_message('Flash Sale Pending ↺ *{}*'.format(database_shop_name))
                    driver.close()
                    driver.switch_to.window(driver.window_handles[1])
                    print('Flash Sale Completed')
                    break
                else:
                    break
    print('Campaign Overview Completed')
    cursor.execute("UPDATE process_time SET execution_time = ? WHERE (shop_name, name) = (?, ?)",
                   (time.strftime("%Y-%m-%d %H:%M:%S"), database_shop_name, 'campaign_overview'))
    conn.commit()


def order_limit():
    print('Order Limit Started')
    load_page('https://sellercenter.daraz.com.bd/order/query?tab=pending', 'table td .next-table-empty')
    try:
        if (wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'table td .next-table-empty')))
                .text == 'No Data'):
            return True
        order_limit_status = driver.find_element(By.CSS_SELECTOR, '.notices-container').text
    except NoSuchElementException:
        order_limit_status = ''
    if ("Please process existing orders in order to continue to receive more orders." in order_limit_status
            and order_limit_status != ''):
        send_message(database_shop_name + ': ' + order_limit_status)
    rts()


def rts():
    print('RTS Started')
    cursor.execute("UPDATE process_time SET execution_time = ? WHERE (shop_name, name) = (?, ?)",
                   (time.strftime("%Y-%m-%d %H:%M:%S"), database_shop_name, 'order_limit'))
    conn.commit()
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
            time.sleep(2)
            wait.until(ec.element_to_be_clickable((By.XPATH, "//button[text()='Save invoice ID']"))).click()
        except TimeoutException:
            pass
        try:
            time.sleep(2)
            wait.until(ec.visibility_of_element_located((By.XPATH, "//button[text()='Ready to ship']")))
            time.sleep(2)
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


def move_click(move_element, click_element):
    mouse.move_to_element(driver.find_element(move_element)).perform()
    driver.find_element(click_element).click()


def redirection_login(page_url, element):
    if 'seller/login' in driver.current_url and 'seller/login' not in page_url:
        driver.switch_to.window(driver.window_handles[1])
        login()
        load_page(page_url, element)
        return True


def load_page(page_url, element='body'):
    global triumph
    if inspect.currentframe().f_back.f_code.co_name != 'load_page':
        triumph = 0
    try:
        driver.get(page_url)
        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, element)))
        # redirection_login(page_url, element)
    except TimeoutException:
        print('Page loading failed: {}'.format(page_url))
        # redirection_login(page_url, element)
        triumph += 1
        if triumph >= 5:
            print('Page loading failed {} times'.format(triumph))
            wait_for_connection()
            if 'chat/window' not in driver.current_url:
                return False
        elif triumph > 10:
            raise Exception('Page loading failed {} times'.format(triumph))
        load_page(page_url, element)
    return True


def question():
    print('Checking question status')
    if not load_page('https://sellercenter.daraz.com.bd/msg/index', '[role="tablist"]'):
        print('Question Page Loading Failed')
        wait_for_connection()
        return False
    try:
        question_element = wait.until(
            ec.presence_of_element_located((By.XPATH, "//div[contains(text(),'Customer Question')]"))).text
        # Get the number of question
        question_count = int(question_element.split('(')[1].split(')')[0])
        if question_count > 0:
            send_message('*{}* has *{}* question(s)'.format(database_shop_name, question_count))
    except Exception as question_error:
        print(question_error)
        return True
    print('Question status checked')
    cursor.execute("UPDATE process_time SET execution_time = ? WHERE (shop_name, name) = (?, ?)",
                   (time.strftime("%Y-%m-%d %H:%M:%S"), database_shop_name, 'question'))
    conn.commit()


def stock_check():
    print('Stock Check Started')
    load_page('https://sellercenter.daraz.com.bd/v2/product/list')
    try:
        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, '.product-list-table')))
    except TimeoutException:
        stock_check()
        return True
    if driver.find_elements(By.CSS_SELECTOR, '.intl-tag-list'):
        send_message('Stock Out ↺ *{}*'.format(database_shop_name))
    cursor.execute("UPDATE process_time SET execution_time = ? WHERE (shop_name, name) = (?, ?)",
                   (time.strftime("%Y-%m-%d %H:%M:%S"), database_shop_name, stock_check.__name__))
    conn.commit()
    print('Stock Check Completed')


def set_browser():
    try:
        wait_for_connection()
        browser_driver = webdriver.Chrome(service=service, options=options)
        browser_driver.implicitly_wait(2)
        # browser_driver.maximize_window()
        browser_driver.set_page_load_timeout(20)
        db_mouse = webdriver.ActionChains(browser_driver)
        driver_wait = WebDriverWait(browser_driver, 10)
        browser_driver.execute_script("window.open('');")
        return browser_driver, driver_wait, db_mouse
    except Exception as browser_error:
        print(browser_error)
        set_browser()


def login_status():
    load_page('https://sellercenter.daraz.com.bd/v2/chat/window')
    if 'chat/window' not in driver.current_url:
        print('Login Failed via cookies')
        login()


def create_instance():
    cursor.execute('SELECT * FROM login_credential')
    drivers_array = []
    waits_array = []
    mouses_array = []
    try:
        for shop_info in cursor.fetchall():
            ins_driver, ins_wait, ins_mouse = set_browser()
            drivers_array.append(ins_driver)
            waits_array.append(ins_wait)
            mouses_array.append(ins_mouse)
            print(shop_info[1] + ' : Instance Created')
    except Exception as instance_error:
        print(instance_error)
        close_instance(drivers_array)
        create_instance()
    return drivers_array, waits_array, mouses_array


def close_instance(drivers_array):
    for current_driver in drivers_array:
        try:
            current_driver.quit()
        except Exception as driver_error:
            print(driver_error)


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
@bot.message_handler(commands=['start', 'info'])
def send_welcome(message):
    stat_db = sqlite3.connect('shop_data.db')
    stat_cursor = stat_db.cursor()
    stat_cursor.execute('SELECT remark FROM login_credential order by remark')
    stat = ''
    for shop_stat in stat_cursor.fetchall():
        stat += "{}\n".format(shop_stat[0])
    bot.send_message(message.chat.id, stat)
    stat_db.close()


@bot.message_handler(commands=['retry'])
def retry(message):
    replied_text = message.reply_to_message.text
    if replied_text.startswith('☠Reply Dropped'):
        query = replied_text.split('🕊')[1].split('➥')[0].strip()
        reply = replied_text.split('➥')[1].split('࿐')[0].strip()
        shop_name = replied_text.split('彡')[1].split('🕊')[0].strip()
        customer_name = replied_text.split('࿐')[1].split('🗝️')[0].strip()
        message_id = int(replied_text.split('🗝️')[1].strip())
        cursor.execute('INSERT INTO external_reply '
                       '(query, reply, shop_name, customer_name, message_id) VALUES (?, ?, ?, ?, ?)',
                       (query, reply, shop_name, customer_name, message_id))
        conn.commit()
        bot.reply_to(message, '_Inserted to retry_࿐')


@bot.message_handler(commands=['debug'])
def send_welcome(message):
    cursor.execute('SELECT value from essentials WHERE name = ?', ('debug',))
    debug_status = bool(int(cursor.fetchone()[0]))
    cursor.execute('UPDATE essentials SET value = ? WHERE name = ?', (not debug_status, 'debug'))
    conn.commit()
    bot.send_message(message.chat.id, '_Debug Mode {}_'.format('On' if not debug_status else 'Off'))


@bot.message_handler(commands=['pause'])
def pause_campaign_alert(message):
    replied_text = message.reply_to_message.text
    try:
        if replied_text.split(' ')[0] == 'Join' and replied_text.split(' ')[1] == 'Campaign':
            campaign_name = replied_text.split('☪')[1].strip()
            shop_name = replied_text.split('彡')[1].split('🪐')[0].strip()
            cursor.execute('UPDATE campaign_alert SET status = ? WHERE name = ? AND shop_name = ?',
                           ('False', campaign_name, shop_name))
            conn.commit()
            bot.reply_to(message, '_Campaign Alert Paused_\n📌{}'.format(to_md(campaign_name)))
            return True
    except Exception as pause_error:
        print(pause_error)
        bot.reply_to(message, '_Can\'t process your reply_࿐')


@bot.message_handler(commands=['clear'])
def pause_campaign_alert(message):
    argument = message.text.split(' ')[1]
    allowed_process = ('send_time', 'external_reply', 'reply_fix', 'campaign_alert')
    if argument in allowed_process:
        cursor.execute('DELETE FROM {} where TRUE'.format(argument))
        conn.commit()
        bot.reply_to(message, '•{}• _Cleared_✄'.format(to_md(argument)))
    else:
        bot.reply_to(message, '_Access not found_ 🗝️')


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    message_text = message.text

    # Check if the message is a reply to another message
    if message.reply_to_message:
        replied_message_text = message.reply_to_message.text
        if not replied_message_text:
            replied_message_text = message.reply_to_message.caption
        # Store replied messages in the database
        store_replied_message(message, chat_id, message_text, replied_message_text)
    else:
        echo_message(chat_id, message_text)


# Function to store replied messages in the database
def store_replied_message(message, chat_id, message_text, replied_message):
    # Create database connection
    external_reply_db = sqlite3.connect('shop_data.db')
    external_reply_cursor = external_reply_db.cursor()

    if replied_message.startswith('✺Extra'):
        replied_message_text = replied_message.split('✺Extra')[1].strip()
    else:
        replied_message_text = replied_message
    try:
        shop_name = replied_message_text.split('♯')[0].strip()
        query = replied_message_text.split('➤')[1].split('࿐')[0].strip()
        customer_name = replied_message_text.split('࿐')[1].strip()
    except IndexError:
        bot.reply_to(message, "_Can't process your reply_࿐")
        # bot.send_message(chat_id, "_Can't process your reply_࿐")
        return True
    if message_text[-1] == '*':
        message_text = message_text[:-1]
        cursor.execute(
            'INSERT INTO reply_fix (reply, shop_name, customer_name, message_id) VALUES (?, ?, ?, ?)',
            (message_text, shop_name, customer_name, message.message_id))
        conn.commit()
        return True
    if message_text[0] == '$':
        message_text = message_text[1:]
        # Store the replied message in the database if already not present
        external_reply_cursor.execute("SELECT * FROM auto_reply WHERE message = ?", (simplified_text(query),))
        if external_reply_cursor.fetchone() is None:
            external_reply_cursor.execute('INSERT INTO auto_reply (message, reply) VALUES (?, ?)',
                                          (simplified_text(query), message_text))
            external_reply_db.commit()
            bot.send_message(chat_id, "_Reply saved successfully_࿐")
            return True
    elif replied_message.startswith('✺Extra'):
        cursor.execute('INSERT INTO reply_fix (reply, shop_name, customer_name, message_id) VALUES (?, ?, ?, ?)',
                       (message_text, shop_name, customer_name, message.message_id))
        conn.commit()
        return True
    external_reply_cursor.execute(
        'INSERT INTO external_reply ('
        'query, reply, shop_name, customer_name, message_id) VALUES (?, ?, ?, ?, ?)',
        (simplified_text(query), message_text, shop_name, customer_name, message.message_id))
    external_reply_db.commit()
    cursor.execute('DELETE FROM send_time WHERE (shop_name, customer_name) = (?, ?)',
                   (shop_name, customer_name))
    conn.commit()


# Function to echo normal replies
def echo_message(chat_id, message_text):
    bot.send_message(chat_id, message_text)


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
# options.add_argument('--blink-settings=imagesEnabled=false')
options.add_argument("--window-size=1280,1080")
options.add_argument("--zoom=1.5")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36")
options.add_argument("--mute-audio")
options.add_argument("--disable-extensions")
options.add_argument("--disable-plugins-discovery")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-infobars")
options.add_argument("--disable-notifications")
options.add_argument("--disable-save-password-bubble")
options.add_argument("--disable-single-click-autofill")
options.add_argument("--disable-translate")
options.add_argument("--disable-webgl")
options.add_argument("--enable-local-file-accesses")
options.add_argument("--enable-automation")
options.add_argument("--enable-javascript")

driver_array, wait_array, mouse_array = create_instance()
# Start a separate thread to continuously check for messages
bot_thread = threading.Thread(target=bot.polling, args=(None,))
bot_thread.start()
print('Message Thread Started')

while True:
    cursor.execute('SELECT * FROM login_credential')
    for row in cursor.fetchall():
        order, database_shop_name, email, password, cookie, remark = row
        driver = driver_array[order - 1]
        wait = wait_array[order - 1]
        mouse = mouse_array[order - 1]
        print(f"ID: {order}\tShop Name: {database_shop_name}")
        try:
            load_cookies(cookie)
            check_message_status()
            driver.switch_to.window(driver.window_handles[1])
            process_list = (('question', 60),
                            ('home_inspection', 0),
                            ('order_limit', 0),
                            ('stock_check', 1440))
            for process in process_list:
                if extra_process and process_time(process[0], process[1], database_shop_name):
                    try:
                        globals()[process[0]]()
                    except Exception as process_error:
                        print(process_error)
                        driver.save_screenshot('Error Screenshot/' + database_shop_name + '.png')
                        wait_for_connection()
                        continue
                    extra_process = False
            if extra_process and process_time('campaign_overview', 0, database_shop_name) and between_time():
                campaign_overview_monitor()
            for msg_shop in cursor.execute('SELECT DISTINCT shop_name FROM external_reply').fetchall():
                print('■━■━■━■ Tunneling for {}'.format(msg_shop[0]))
                cursor.execute('SELECT serial FROM external_reply WHERE shop_name = ?', (msg_shop[0],))
                msg_id = cursor.fetchall()
                order, database_shop_name, email, password, cookie, remark, driver, wait, mouse = (
                    instance_data(msg_shop[0], driver_array, wait_array, mouse_array))
                load_cookies(cookie)
                if not check_message_status():
                    continue
                for msg_serial in msg_id:
                    cursor.execute('SELECT * FROM external_reply WHERE serial = ?', (msg_serial[0],))
                    msg_info = cursor.fetchone()
                    if msg_info is None:
                        continue
                    cursor.execute('DELETE FROM external_reply WHERE serial = ?', (msg_serial[0],))
                    conn.commit()
                    bot.send_message('1783177827', '*☠Reply Dropped* 彡{} 🕊{} ➥{}\n࿐{} 🗝️{}'.
                                     format(msg_info[3], msg_info[1], to_md(msg_info[2]), msg_info[4],
                                            msg_info[5]), reply_to_message_id=msg_info[5])
                print('■━■━■━■ Tunneling Completed')

            for fix_msg_shop in cursor.execute('SELECT DISTINCT shop_name FROM reply_fix').fetchall():
                print('■━■━■━■ Fix Tunneling for {}'.format(fix_msg_shop[0]))
                order, database_shop_name, email, password, cookie, remark, driver, wait, mouse = (
                    instance_data(fix_msg_shop[0], driver_array, wait_array, mouse_array))
                load_cookies(cookie)
                fix_reply()
                print('■━■━■━■ Fix Tunneling Completed')
        except Exception as error:
            try:
                send_message('*☠Error* 彡{} ☄ {}'.format(database_shop_name, type(error).__name__))
            except Exception as error_info:
                print(error_info)
            print(error)
            driver.save_screenshot('Error Screenshot/' + database_shop_name +
                                   time.strftime(" %Y%m%d-%H%M%S") + '.png')
            close_instance(driver_array)
            driver_array, wait_array, mouse_array = create_instance()
        conn.commit()
        if not bot_thread.is_alive():
            bot_thread = threading.Thread(target=bot.polling, args=(None,))
            bot_thread.start()
            print('Message Thread Restarted')
    print('{}'.format(' Cycle Completed '.center(40, '━')))
    if process_time('campaign_alert', 0, 'Generic'):
        campaign_alert()
    cursor.execute('DELETE FROM send_time WHERE send_time < ?',
                   (datetime.now() - timedelta(minutes=30),))
    conn.commit()
    extra_process = True
