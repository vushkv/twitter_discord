import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
from confluent_kafka import Producer, Consumer
from config import producer_config, consumer_config, twitter_username, twitter_password, webdriver_path, following_twitter, confirm_subscription


producer = Producer(producer_config)
consumer = Consumer(consumer_config)
consumer.subscribe([following_twitter])


def login_to_twitter(driver, username, password):
    driver.get('https://x.com/i/flow/login')
    time.sleep(10)
    username_field = driver.find_element(By.CSS_SELECTOR, '#layers > div > div > div > div > div > div > div.css-175oi2r.r-1ny4l3l.r-18u37iz.r-1pi2tsx.r-1777fci.r-1xcajam.r-ipm5af.r-g6jmlv.r-1awozwy > div.css-175oi2r.r-1wbh5a2.r-htvplk.r-1udh08x.r-1867qdf.r-kwpbio.r-rsyp9y.r-1pjcn9w.r-1279nm1 > div > div > div.css-175oi2r.r-1ny4l3l.r-6koalj.r-16y2uox.r-kemksi.r-1wbh5a2 > div.css-175oi2r.r-16y2uox.r-1wbh5a2.r-f8sm7e.r-13qz1uu.r-1ye8kvj > div > div > div > div.css-175oi2r.r-1mmae3n.r-1e084wi.r-13qz1uu > label > div > div.css-175oi2r.r-18u37iz.r-16y2uox.r-1wbh5a2.r-1wzrnnt.r-1udh08x.r-xd6kpl.r-is05cd.r-ttdzmv > div > input')
    username_field.send_keys(username)
    time.sleep(3)
    username_field.send_keys(Keys.RETURN)
    time.sleep(2)
    password_field = driver.find_element(By.CSS_SELECTOR, "#layers > div > div > div > div > div > div > div.css-175oi2r.r-1ny4l3l.r-18u37iz.r-1pi2tsx.r-1777fci.r-1xcajam.r-ipm5af.r-g6jmlv.r-1awozwy > div.css-175oi2r.r-1wbh5a2.r-htvplk.r-1udh08x.r-1867qdf.r-kwpbio.r-rsyp9y.r-1pjcn9w.r-1279nm1 > div > div > div.css-175oi2r.r-1ny4l3l.r-6koalj.r-16y2uox.r-kemksi.r-1wbh5a2 > div.css-175oi2r.r-16y2uox.r-1wbh5a2.r-f8sm7e.r-13qz1uu.r-1ye8kvj > div.css-175oi2r.r-16y2uox.r-1wbh5a2.r-1dqxon3 > div > div > div.css-175oi2r.r-1e084wi.r-13qz1uu > div > label > div > div.css-175oi2r.r-18u37iz.r-16y2uox.r-1wbh5a2.r-1wzrnnt.r-1udh08x.r-xd6kpl.r-is05cd.r-ttdzmv > div.css-146c3p1.r-bcqeeo.r-1ttztb7.r-qvutc0.r-37j5jr.r-135wba7.r-16dba41.r-1awozwy.r-6koalj.r-1inkyih.r-13qz1uu > input")
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)


def check_following(driver, user, target):
    driver.get(f'https://x.com/{user}/following')
    time.sleep(5)
    try:
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        following_elements = driver.find_elements(By.CSS_SELECTOR, 'span.css-1jxf684.r-bcqeeo.r-1ttztb7.r-qvutc0.r-poiln3')
        for element in following_elements:
            try:
                user_handle = element.text
                if user_handle.lower() == f'@{target}'.lower():
                    return 'success'
            except:
                continue

        return 'fail'
    except Exception as e:
        print(f"Error: {e}")
        return 'Unknown'

def send_message(topic, key, message):
    producer.produce(topic, key=key, value=message)
    producer.flush()

def main():
    service = Service(webdriver_path)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=options)

    try:
        login_to_twitter(driver, twitter_username, twitter_password)
        WebDriverWait(driver, 10).until(EC.url_contains('home'))

        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue

            try:
                data = json.loads(msg.value().decode('utf-8'))
                user = data.get('user')
                target = data.get('target')

                if user and target:
                    status = check_following(driver, user, target)
                    send_message(confirm_subscription, key=msg.key(), message=status)
                else:
                    print("Invalid message format: missing 'user' or 'target'")
            except json.JSONDecodeError as e:
                print(f"Failed to decode JSON: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()