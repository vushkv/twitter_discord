import json
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
from confluent_kafka import Producer, Consumer
from selenium.webdriver.chrome.service import Service
from config import producer_config, consumer_config, twitter_username, twitter_password, webdriver_path, post_twitter, twit_status
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException


producer = Producer(producer_config)
consumer = Consumer(consumer_config)
consumer.subscribe([post_twitter])

def login_to_twitter(driver, twitter_username, twitter_password):
    driver.get("https://twitter.com/login")
    time.sleep(10)

    username_field = driver.find_element(By.CSS_SELECTOR,
                                         '#layers > div > div > div > div > div > div > div.css-175oi2r.r-1ny4l3l.r-18u37iz.r-1pi2tsx.r-1777fci.r-1xcajam.r-ipm5af.r-g6jmlv.r-1awozwy > div.css-175oi2r.r-1wbh5a2.r-htvplk.r-1udh08x.r-1867qdf.r-kwpbio.r-rsyp9y.r-1pjcn9w.r-1279nm1 > div > div > div.css-175oi2r.r-1ny4l3l.r-6koalj.r-16y2uox.r-kemksi.r-1wbh5a2 > div.css-175oi2r.r-16y2uox.r-1wbh5a2.r-f8sm7e.r-13qz1uu.r-1ye8kvj > div > div > div > div.css-175oi2r.r-1mmae3n.r-1e084wi.r-13qz1uu > label > div > div.css-175oi2r.r-18u37iz.r-16y2uox.r-1wbh5a2.r-1wzrnnt.r-1udh08x.r-xd6kpl.r-is05cd.r-ttdzmv > div > input')
    username_field.send_keys(twitter_username)
    time.sleep(3)
    username_field.send_keys(Keys.RETURN)
    time.sleep(2)

    password_field = driver.find_element(By.CSS_SELECTOR,
                                         "#layers > div > div > div > div > div > div > div.css-175oi2r.r-1ny4l3l.r-18u37iz.r-1pi2tsx.r-1777fci.r-1xcajam.r-ipm5af.r-g6jmlv.r-1awozwy > div.css-175oi2r.r-1wbh5a2.r-htvplk.r-1udh08x.r-1867qdf.r-kwpbio.r-rsyp9y.r-1pjcn9w.r-1279nm1 > div > div > div.css-175oi2r.r-1ny4l3l.r-6koalj.r-16y2uox.r-kemksi.r-1wbh5a2 > div.css-175oi2r.r-16y2uox.r-1wbh5a2.r-f8sm7e.r-13qz1uu.r-1ye8kvj > div.css-175oi2r.r-16y2uox.r-1wbh5a2.r-1dqxon3 > div > div > div.css-175oi2r.r-1e084wi.r-13qz1uu > div > label > div > div.css-175oi2r.r-18u37iz.r-16y2uox.r-1wbh5a2.r-1wzrnnt.r-1udh08x.r-xd6kpl.r-is05cd.r-ttdzmv > div.css-146c3p1.r-bcqeeo.r-1ttztb7.r-qvutc0.r-37j5jr.r-135wba7.r-16dba41.r-1awozwy.r-6koalj.r-1inkyih.r-13qz1uu > input")
    password_field.send_keys(twitter_password)
    password_field.send_keys(Keys.RETURN)
    time.sleep(5)


def check_for_tweet(driver, user, target):
    driver.get(f"https://twitter.com/{user}")
    time.sleep(5)

    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        tweets = driver.find_elements(By.XPATH, '//div[@data-testid="tweetText"]')
        for tweet in tweets:
            if target in tweet.text:
                return True

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        try:
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.body.scrollHeight") > last_height
            )
        except TimeoutException:
            break

        last_height = driver.execute_script("return document.body.scrollHeight")

    return False

def send_message(topic, message, key):
    producer.produce(topic, value=message, key=key)
    producer.flush()

def main():
    service = Service(webdriver_path)
    driver = webdriver.Chrome(service=service)

    try:
        login_to_twitter(driver, twitter_username, twitter_password)

        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue

            try:
                key = msg.key().decode('utf-8') if msg.key() else None
                data = json.loads(msg.value().decode('utf-8'))
                user = data.get('user')
                target = data.get('target')

                if user and target:
                    found = check_for_tweet(driver, user, target)
                    status = 'success' if found else 'fail'
                    send_message(twit_status, status, key)
                else:
                    print("Invalid message format: missing 'target' or 'text'")
            except json.JSONDecodeError as e:
                print(f"Failed to decode JSON: {e}")

    finally:
        driver.quit()
        consumer.close()

if __name__ == "__main__":
    main()