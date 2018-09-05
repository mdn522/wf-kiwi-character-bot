__author__ = "mdn522"
__copyright__ = "Copyright 2018"
__license__ = "GPL"
__version__ = "1.7.6"
__maintainer__ = "mdn522"
__status__ = "beta"

import os
import json
import re
import time
from datetime import datetime
import pause
import sys
import pickle
import signal

import logging
import winsound

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# I am too lazy organize the code
print('K.I.W.I Character Automator Bot')
print('Developed by: Abdullah Mallik (@mdn522)')

debug = True
error = True
info = True

# VARS
# Set value in info.json
mission_file = None
task_name = None
stars = None
energy_usages = None
can_send = None
refill = None
refill_min_bp = None
refill_min_energy = None
refill_drain = None
refill_drain_map = None
switch_based_on_energy = None
switch_min_energy = None
switch_to_stars = None
switch_to_mission_file = None
switch_to_task_name = None
refresh_before_switch = None
energy_shortage_exit = None
energy_shortage_wait = None
refresh_min_time = None
log_to_file = None
hide_browser = None


class UnhandledElseClause(Exception):
    pass


logging.basicConfig(level=logging.DEBUG, filename='debug.log')


def reload_vars():
    try:
        # Load vars from info.json
        with open('info.json') as fp:
            obj = json.load(fp)
            globals().update(obj)
            # for k, v in obj.items():
            #     globals()[k] = v

    except Exception as e:
        not error or print(e)


def refresh_kiwi(force=False):
    global driver, last_time_refreshed, refresh_min_time

    if force or (int(datetime.now().timestamp()) - last_time_refreshed) >= refresh_min_time:
        print('Refreshing K.I.W.I. page')
        driver.get('http://wf.my.com/kiwi')
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.app.user'))
        )
        time.sleep(1)
        reload_ebp()
        last_time_refreshed = int(datetime.now().timestamp())

    
def save_cookies(driver, filename):
    pickle.dump(driver.get_cookies() , open(filename, "wb"))


def load_cookies(driver, filename):
    cookies = pickle.load(open(filename, "rb"))
    for cookie in cookies:
        driver.add_cookie(cookie)


def promp_user_to_login():
    options = webdriver.ChromeOptions()
    cap = DesiredCapabilities.CHROME

    options.add_argument("user-data-dir=chrome_profile")

    options.add_argument('log-level=3')
    options.add_argument("--start-maximized")

    login_driver = webdriver.Chrome(chrome_options=options, desired_capabilities=cap)

    login_driver.get('https://wf.my.com/')

    print('Looks like you are not logged in or logged out.')
    input('Please login and hit enter\n')

    save_cookies(login_driver, 'cookies.pkl')

    login_driver.quit()


def get_task_window(mission_file, task_name, check=False):
    global driver
    
    def _get_active_task_window():
        return driver.find_element_by_css_selector('.tasks__window.outline.double_mix_border.corner_big.avatar')
    
    try:
        active_task_window = _get_active_task_window()
    except: pass
    else:
        if (check and active_task_window.find_element_by_css_selector('.tasks__info__top.avatar > h4').get_attribute('innerHTML').lower() == task_name.lower()) or not check:
            return active_task_window
    
    # Send esc
    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    
    time.sleep(0.1)
    
    # Click File Icon
    # driver.find_element_by_css_selector('.map__point.squares.corner_big.white.point-{}'.format(mission_file)).click()
    WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '.map__point.squares.corner_big.white.point-{}'.format(mission_file)))
    ).click()

    time.sleep(0.5)
    
    # Click Start Button
    # driver.find_element_by_css_selector('.map__point.squares.corner_big.white.point-{} .map__point__options > .button.button--white'.format(mission_file)).click()
    WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '.map__point.squares.corner_big.white.point-{} .map__point__options > .button.button--white'.format(mission_file)))
    ).click()

    time.sleep(2)
    
    # Click Task Button
    WebDriverWait(driver.find_element_by_class_name('tasks'), 15).until(
        EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '{}')]".format(task_name.title())))
    ).click()

    time.sleep(0.1)
    
    task_window = _get_active_task_window() 
    
    return task_window


def printl(msg):
    global log_to_file
    s = datetime.today().strftime("%Y-%m-%d %I:%M %p") + ': ' + msg

    print(s)

    if log_to_file:
        with open('logs.txt', 'a+', encoding='utf-8') as fp:
            fp.write(s + '\n')


def get_active_mission_file(driver):
    return re.search('anubis|icebreaker|pripyat|shark|volcano', 
                     driver.find_element_by_class_name('tasks').get_attribute('class')).group()


def get_active_task_name(task_window):
    return task_window.find_element_by_css_selector('.tasks__info__top.avatar > h4').get_attribute('innerHTML').lower()


def get_active_stars(task_window):
    global stars
    current_stars = stars
    stars_io = ['active' in el.get_attribute('class') for el in task_window.find_elements_by_css_selector('.stars_container > .stars_list')]
    for i in range(len(stars_io)):
        if stars_io[i]:
            current_stars = i + 1
            break
    return current_stars


def reload_ebp():
    global driver, energy, bp

    energy = int(driver.execute_script('return document.querySelector(".app.energy > .value").innerHTML').strip('%'))
    bp = int(driver.execute_script('return document.querySelector(".app.points > .value").innerHTML'))


def refill_energy():
    global driver

    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()

    time.sleep(0.1)

    driver.find_element_by_css_selector('.app.energy > .button.button--plus').click()
    
    time.sleep(0.1)

    energy_purchase = driver.find_element_by_class_name('buy-energy__purchase')

    try:
        webdriver.ActionChains(driver).click_and_hold(energy_purchase).perform()

        time.sleep(1)

        webdriver.ActionChains(driver).release(energy_purchase).perform()
    except Exception as e:
        not error or print(e)


reload_vars()

options = webdriver.ChromeOptions()
cap = DesiredCapabilities.CHROME
# cap["pageLoadStrategy"] = "none"

if hide_browser:
    options.add_argument("--headless")
    options.add_argument("user-data-dir=headless_chrome_profile")

    cap['acceptSslCerts'] = True
    cap['acceptInsecureCerts'] = True
else:
    options.add_argument("user-data-dir=chrome_profile")

options.add_argument('log-level=3')
options.add_argument("--start-maximized")

driver = webdriver.Chrome(chrome_options=options, desired_capabilities=cap)

driver.get('https://wf.my.com/kiwi')

if not hide_browser:
    input('''Do these steps
(1) Login in to your my.com account
(2) Open KIWI page
(3) Open desired character task
(4) Start the character task (if not already)
(5) Press enter
''')
else:
    logged_in = False

    while not logged_in:
        try:
            load_cookies(driver, 'cookies.pkl')
            driver.get('https://wf.my.com/kiwi')
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'userinfo'))
            )
            logged_in = True
        except Exception as e:
            promp_user_to_login()

energy = int(WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, '.energy > .value'))
).text.strip('%'))
bp = int(driver.find_element_by_css_selector('.points > .value').text)


if not hide_browser:
    not info or print('Saving cookies for headless session.')
    save_cookies(driver, 'cookie.pkl')


last_time_refreshed = int(datetime.now().timestamp())

exc_on_streak = False
exc_count = 0
exc_refresh_after = 5

print('Bot Started...')

while True:
    reload_vars()

    try:
        if exc_on_streak and exc_count >= exc_refresh_after:
            exc_count = 0
            exc_on_streak = False
            refresh_kiwi(True)

        reload_ebp()

        task_window = get_task_window(mission_file, task_name)

        if task_window.find_elements_by_class_name('timer__text'):  # Task in progress
            time_remaining = tr = task_window.find_element_by_class_name('timer__text').text
            if ':' in time_remaining:  # h:m
                time_remaining = int(tr.split(':')[0]) * 3600 + int(tr.split(':')[1]) * 60
            else:  # s
                time_remaining = int(time_remaining)
            pause.seconds(time_remaining + 10)

        elif task_window.find_elements_by_class_name('avatar__reward'):  # Task finished
            log_prefix = "{:10} -> {:10} {} -> ".format(get_active_mission_file(driver).title(), get_active_task_name(task_window).upper(), '(' + (get_active_stars(task_window) * '★') + ')')
            task_reward = task_window.find_element_by_class_name('avatar__reward')

            if task_reward.find_elements_by_class_name('failed'):  # Task failed
                printl(log_prefix + 'Task Failed')
            else:  # Task passed
                reward_text = task_reward.find_element_by_class_name('name').text

                if task_window.find_elements_by_class_name('time'):
                    reward_text += " (%s)" % (task_window.find_element_by_class_name('time').text)

                printl(log_prefix + 'Task Reward ' + reward_text)

            # Click close button
            # task_reward.find_element_by_css_selector('.button.button--white').click()
            WebDriverWait(task_reward, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.button.button--white'))
            ).click()

        elif task_window.find_elements_by_css_selector('div.bottom > div.button_container > div.button.button--white'):  # Free state
            if can_send:  # and (send_until_energy and energy > send_until_energy):
                current_stars = stars

                switched = False
                if switch_based_on_energy and energy <= switch_min_energy and (not stars == switch_to_stars or (switch_to_task_name and not task_name == switch_to_task_name)):
                    if refresh_before_switch:
                        refresh_kiwi()

                    if energy <= switch_min_energy:
                        switch_log = (
                            (mission_file == switch_to_mission_file) if mission_file else True,
                            task_name == switch_to_task_name,
                            current_stars == switch_to_stars,
                        )

                        current_stars = switch_to_stars or stars
                        mission_file = switch_to_mission_file or mission_file
                        task_name = switch_to_task_name or task_name

                        switched = True

                        print('Switched task to {:11} -> {:11} {} because current energy is less than {}'.format(
                            mission_file.title() + ('*' if not switch_log[0] else ''),
                            task_name.upper() + ('*' if not switch_log[1] else ''), 
                            '(' + current_stars * '★' + ')' + ('*' if switch_log[2] else ''), 
                            switch_min_energy + 1))

                task_window = get_task_window(mission_file, task_name, check=True)

                energy_usage = energy_usages[stars - 1]
                if energy < energy_usage:  # energy shortage
                    refresh_kiwi()
                    task_window = get_task_window(mission_file, task_name, check=True)

                    if energy < energy_usage:  # still energy shortage
                        print('Still energy shortage after refreshing (%s energy)' % (energy,))
                        if refill:
                            refill_drain_star_map = [i for i in refill_drain_map if energy_usages[i - 1] <= energy]
                            if refill_drain and refill_drain_star_map:  # Drain energy
                                current_stars = refill_drain_star_map[0]
                                print('Draining energy with %d star' % (current_stars,))
                            elif refill_min_energy >= energy and bp >= max(50, refill_min_bp):  # Refill
                                print('Refilling energy')
                                refill_energy()
                                last_time_refreshed = int(datetime.now().timestamp())
                                continue

                                # task_window = get_task_window(mission_file, task_name, check=True)
                            else:
                                print('Waiting for {} second(s) for energy'.format(energy_shortage_wait))
                                pause.seconds(energy_shortage_wait)
                                continue

                        elif energy_shortage_exit:
                            print('Exiting because of energy shortage...')
                            break
                        elif not energy_shortage_exit:
                            pause.seconds(energy_shortage_wait)
                            continue

                # Select stars
                task_window.find_elements_by_css_selector('.stars_container > .stars_list')[current_stars - 1].click()

                # Send
                # task_window.find_element_by_css_selector('.button.button--white').click()
                WebDriverWait(task_window, 15).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.button.button--white'))
                ).click()

                time.sleep(1)
            else:
                print('I have no permission to start the task :(\nExiting...')
                break
        else:
            pause.seconds(3)
            raise UnhandledElseClause
    except KeyboardInterrupt:
        print('User forced to exit...')
        break
    except UnhandledElseClause:
        exc_count += 1
        exc_on_streak = True
    except Exception as e:
        not error or print(e)
            
        logging.exception("Exception!")

        exc_count += 1
        exc_on_streak = True

        time.sleep(5)
    else:
        exc_count = 0
        exc_on_streak = False

driver.quit()

# Beep
winsound.Beep(850, 1)