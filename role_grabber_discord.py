from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from confluent_kafka import Consumer, Producer
import json
import time
from config import producer_config, consumer_config, discord_username, discord_password, discord_server, webdriver_path, role_user_discord, list_roles, role_discord


producer = Producer(producer_config)
consumer = Consumer(consumer_config)
consumer.subscribe([role_user_discord])


def login_to_discord(driver):
    driver.get('https://discord.com/login')

    time.sleep(5)

    username_field = driver.find_element(By.NAME, "email")
    username_field.send_keys(discord_username)

    password_field = driver.find_element(By.NAME, "password")
    password_field.send_keys(discord_password)
    password_field.send_keys(Keys.RETURN)

    time.sleep(10)


def scroll_and_find_user(driver, username):
    role_texts = []
    while True:
        try:
            user_element = driver.find_element(By.XPATH, f"//span[text()='{username}']")
            ActionChains(driver).move_to_element(user_element).click().perform()
            time.sleep(5)

            try:
                role_elements = driver.find_elements(By.CSS_SELECTOR, "[aria-label]")
                for role_element in role_elements:
                    aria_label = role_element.get_attribute("aria-label")
                    if aria_label and aria_label in list_roles:
                        role_texts.append(aria_label)
            except NoSuchElementException:
                print("Роли не найдены.")
            break
        except NoSuchElementException:
            user_list = driver.find_element(By.CSS_SELECTOR,
                                            '#app-mount > div.appAsidePanelWrapper_bd26cc > div.notAppAsidePanel_bd26cc > div.app_bd26cc > div > div.layers_d4b6c5.layers_a01fb1 > div > div > div > div.content_a4d4d9 > div.chat_a7d72e > div.content_a7d72e > div > aside > div')
            driver.execute_script("arguments[0].scrollTop += arguments[0].offsetHeight;", user_list)
            time.sleep(2)
    return role_texts


def check_account_exists(driver, username):
    driver.get(f"https://discord.com/channels/{discord_server}")
    time.sleep(5)

    peoples = driver.find_element(By.CSS_SELECTOR,
                                  "#app-mount > div.appAsidePanelWrapper_bd26cc > div.notAppAsidePanel_bd26cc > div.app_bd26cc > div > div.layers_d4b6c5.layers_a01fb1 > div > div > div > div.content_a4d4d9 > div.chat_a7d72e > div.subtitleContainer_a7d72e > section > div > div.toolbar_fc4f04 > div:nth-child(4) > svg")
    peoples.click()
    time.sleep(5)

    roles = scroll_and_find_user(driver, username)
    return roles


def process_message(driver, message):
    data = json.loads(message.value().decode('utf-8'))
    username = data.get('user')

    if not username:
        return

    roles = check_account_exists(driver, username)
    return roles


def main():

    service = Service(webdriver_path)
    driver = webdriver.Chrome(service=service)
    login_to_discord(driver)


    while True:
        msg = consumer.poll(timeout=1.0)

        if msg is None:
            continue

        if msg.error():
            print(f"Ошибка: {msg.error()}")
            continue

        key = msg.key().decode('utf-8') if msg.key() else None

        roles = process_message(driver, msg)

        if roles:
            producer.produce(role_discord, key=key, value=json.dumps(roles))
            producer.flush()

if __name__ == "__main__":
    main()