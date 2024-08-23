import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import time
from confluent_kafka import Producer, Consumer
from config import producer_config, consumer_config, webdriver_path, discord_username, discord_password, discord_server, following_discord, confirm_subscription

producer = Producer(producer_config)
consumer = Consumer(consumer_config)
consumer.subscribe([following_discord])


def login_to_discord(driver, discord_username, discord_password):
    driver.get('https://discord.com/login')
    time.sleep(10)

    username_field = driver.find_element(By.CSS_SELECTOR, "#uid_7")
    username_field.send_keys(discord_username)

    password_field = driver.find_element(By.CSS_SELECTOR, "#uid_9")
    password_field.send_keys(discord_password)

    password_field.send_keys(Keys.RETURN)
    time.sleep(5)


def check_user_on_server(driver, username):
    driver.get(f"https://discord.com/channels/{discord_server}")
    time.sleep(5)

    peoples = driver.find_element(By.CSS_SELECTOR, "#app-mount > div.appAsidePanelWrapper_bd26cc > div.notAppAsidePanel_bd26cc > div.app_bd26cc > div > div.layers_d4b6c5.layers_a01fb1 > div > div > div > div.content_a4d4d9 > div.chat_a7d72e > div.subtitleContainer_a7d72e > section > div > div.toolbar_fc4f04 > div:nth-child(4) > svg")
    peoples.click()
    time.sleep(5)

    try:
        last_height = driver.execute_script("return arguments[0].scrollHeight",
                                            driver.find_element(By.CSS_SELECTOR, 'div.scroller-1JbKMe'))

        while True:
            driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);",
                                  driver.find_element(By.CSS_SELECTOR, 'div.scroller-1JbKMe'))
            time.sleep(3)

            new_height = driver.execute_script("return arguments[0].scrollHeight",
                                               driver.find_element(By.CSS_SELECTOR, "#app-mount > div.appAsidePanelWrapper_bd26cc > div.notAppAsidePanel_bd26cc > div.app_bd26cc > div > div.layers_d4b6c5.layers_a01fb1 > div > div > div > div > div.chat_a7d72e > div.content_a7d72e > div > aside > div > div"))
            if new_height == last_height:
                break
            last_height = new_height

        name_elements = driver.find_elements(By.CSS_SELECTOR, "#app-mount > div.appAsidePanelWrapper_bd26cc > div.notAppAsidePanel_bd26cc > div.app_bd26cc > div > div.layers_d4b6c5.layers_a01fb1 > div > div > div > div.content_a4d4d9 > div.chat_a7d72e > div.content_a7d72e > div > aside > div > div")
        for element in name_elements:
            if element.text.lower() == username.lower():
                return True
        return False
    except Exception as e:
        print(f"Error: {e}")
        return 'Unknown'


def send_message(topic, key, message):
    producer.produce(topic, key=key, value=message.encode('utf-8'))
    producer.flush()


def main():
    service = Service(webdriver_path)
    driver = webdriver.Chrome(service=service)

    try:
        login_to_discord(driver, discord_username, discord_password)

        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue

            try:
                data = json.loads(msg.value().decode('utf-8'))
                target_username = data.get('user')

                if target_username:
                    exists = check_user_on_server(driver, target_username)
                    status = 'success' if exists else 'fail'
                    send_message(confirm_subscription, key=msg.key(), message=status)
                else:
                    print("Invalid message format: missing 'user'")
            except json.JSONDecodeError as e:
                print(f"Failed to decode JSON: {e}")

    finally:
        driver.quit()
        consumer.close()


if __name__ == "__main__":
    main()