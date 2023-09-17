from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

# set chrome driver
service = Service('driver/chromedriver.exe')
driver = webdriver.Chrome(service=service)
driver.implicitly_wait(10)
driver.maximize_window()
wait = WebDriverWait(driver, 100)

driver.get('https://www.daraz.com.bd/products/uiisii-c100-i118458553-s1037798173.html')


def scrap():
    reviews = wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, '.mod-reviews .item')))
    for review in reviews:
        print(review.find_element(By.CSS_SELECTOR, '.content').text)


while True:
    try:
        scrap()
        actions = ActionChains(driver)
        actions.move_to_element(driver.find_element(By.CSS_SELECTOR, '.review-pagination .next'))
        actions.perform()
        wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, '.review-pagination .next'))).click()
        driver.implicitly_wait(1000)
    except Exception as e:
        print(e)
        break

# prevent browser from closing
input('Press ENTER to close the automated browser')
