from datetime import date
from constants.xPaths import *
from constants.urls import *
from constants.parser import *
from constants.location import *
from constants.email import *
from constants.elementIds import *
from constants.classNames import *
from constants.fileNames import *
from constants.common import *
import requests
import functools
import os
import subprocess
import random
import sys
import time
import string
from selenium.webdriver.chrome import options

import speech_recognition as sr
from faker import Faker
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from constants.areaCodes import AREA_CODES

from resume_faker import make_resume
from password_generator import PasswordGenerator


from webdriver_manager.chrome import ChromeDriverManager
os.environ['WDM_LOG_LEVEL'] = '0'


today = date.today()

# Adds /usr/local/bin to my path which is where my ffmpeg is stored
os.environ["PATH"] += ":/usr/local/bin"

fake = Faker()

# Add printf: print with flush by default. This is for python 2 support.
# https://stackoverflow.com/questions/230751/how-can-i-flush-the-output-of-the-print-function-unbuffer-python-output#:~:text=Changing%20the%20default%20in%20one%20module%20to%20flush%3DTrue
printf = functools.partial(print, flush=True)

r = sr.Recognizer()


def audioToText(mp3Path):
    # deletes old file
    try:
        os.remove(CAPTCHA_WAV_FILENAME)
    except FileNotFoundError:
        pass
    # convert wav to mp3
    subprocess.run(
        f"ffmpeg -i {mp3Path} {CAPTCHA_WAV_FILENAME}", shell=True, timeout=5)

    with sr.AudioFile(CAPTCHA_WAV_FILENAME) as source:
        audio_text = r.listen(source)
        try:
            text = r.recognize_google(audio_text)
            printf('Converting audio transcripts into text ...')
            return(text)
        except Exception as e:
            printf(e)
            printf('Sorry.. run again...')


def random_phone(format=None):
    area_code = str(random.choice(AREA_CODES))
    middle_three = str(random.randint(0, 999)).rjust(3, '0')
    last_four = str(random.randint(0, 9999)).rjust(4, '0')

    if format is None:
        format = random.randint(0, 4)

    if format == 0:
        return area_code+middle_three+last_four
    elif format == 1:
        return area_code+' '+middle_three+' '+last_four
    elif format == 2:
        return area_code+'.'+middle_three+'.'+last_four
    elif format == 3:
        return area_code+'-'+middle_three+'-'+last_four
    elif format == 4:
        return '('+area_code+') '+middle_three+'-'+last_four


def gen_password():
    let = list(string.ascii_letters)
    num = list(string.digits)
    characters = list(string.ascii_letters + string.digits + "!@#$%^&*()")

    length = random.randint(6, 30)

    password = []
    for i in range(length):
        x = random.choice(characters)
        if x not in password:
            password.append(x)
        else:
            i = i-1

    x = random.choice(let)
    if not x in password:
        x.capitalize()
        password.append(x)

    x = random.choice(num)
    if x not in password:
        password.append(x)

    random.shuffle(password)
    return "".join(password)


def saveFile(content, filename):
    with open(filename, "wb") as handle:
        for data in content.iter_content():
            handle.write(data)
# END TEST


def solveCaptcha(driver):
    # Logic to click through the reCaptcha to the Audio Challenge, download the challenge mp3 file, run it through the audioToText function, and send answer
    googleClass = driver.find_elements_by_class_name(CAPTCHA_BOX)[0]
    time.sleep(2)
    outeriframe = googleClass.find_element_by_tag_name('iframe')
    time.sleep(1)
    outeriframe.click()
    time.sleep(2)
    allIframesLen = driver.find_elements_by_tag_name('iframe')
    time.sleep(1)
    audioBtnFound = False
    audioBtnIndex = -1
    for index in range(len(allIframesLen)):
        driver.switch_to.default_content()
        iframe = driver.find_elements_by_tag_name('iframe')[index]
        driver.switch_to.frame(iframe)
        driver.implicitly_wait(2)
        try:
            audioBtn = driver.find_element_by_id(
                RECAPTCHA_AUDIO_BUTTON) or driver.find_element_by_id(RECAPTCHA_ANCHOR)
            audioBtn.click()
            audioBtnFound = True
            audioBtnIndex = index
            break
        except Exception as e:
            pass
    if audioBtnFound:
        try:
            while True:
                """
                try:
                    time.sleep(3)
                    WebDriverWait(driver, 20).until(expected_conditions.presence_of_element_located((By.ID, AUDIO_SOURCE)))
                except Exception as e:
                    print(f"Waiting broke lmao {e}")
                """
                driver.implicitly_wait(10)
                href = driver.find_element_by_id(
                    AUDIO_SOURCE).get_attribute('src')
                response = requests.get(href, stream=True)
                saveFile(response, CAPTCHA_MP3_FILENAME)
                response = audioToText(CAPTCHA_MP3_FILENAME)
                printf(response)
                driver.switch_to.default_content()
                iframe = driver.find_elements_by_tag_name('iframe')[
                    audioBtnIndex]
                driver.switch_to.frame(iframe)
                inputbtn = driver.find_element_by_id(AUDIO_RESPONSE)
                inputbtn.send_keys(response)
                inputbtn.send_keys(Keys.ENTER)
                time.sleep(2)
                errorMsg = driver.find_elements_by_class_name(
                    AUDIO_ERROR_MESSAGE)[0]
                if errorMsg.text == "" or errorMsg.value_of_css_property('display') == 'none':
                    printf("reCaptcha defeated!")
                    break
        except Exception as e:
            printf(e)
            printf('Oops, something happened. Check above this message for errors or check the chrome window to see if captcha locked you out...')
    else:
        printf('Button not found. This should not happen.')

    time.sleep(2)
    driver.switch_to.default_content()


def start_driver(random_city):

    driver = webdriver.Chrome(ChromeDriverManager().install())

    driver.get(CITIES_TO_URLS[random_city])
    driver.implicitly_wait(10)
    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((By.XPATH, APPLY_NOW_BUTTON_1)))
    driver.find_element_by_xpath(APPLY_NOW_BUTTON_1).click()
    driver.find_element_by_xpath(PRIVACY_ACCEPT).click()
    driver.find_element_by_xpath(NEW_CANIDATE_BUTTON).click()
    return driver


def generate_account(driver, fake_identity):
    # make fake account info and fill

    info = ''
    email = fake.free_email()
    pwo = PasswordGenerator()
    password = gen_password()

    for key in XPATHS_1.keys():
        if key in ('email', 'email-retype'):
            info = fake_identity['email']
        elif key in ('pass', 'pass-retype'):
            info = password + "X!"
        elif key == 'username':
            info = fake_identity['first_name'] + \
                fake_identity['last_name'] + str(random.randint(0, 10000))

        driver.find_element_by_xpath(XPATHS_1.get(key)).send_keys(info)

    driver.find_element_by_xpath(REGISTER_ACCOUNT).click()

    try:
        element_present = expected_conditions.presence_of_element_located(
            (By.ID, 'et-ef-content-ftf-gp-j_id_id16pc9-page_0-cpi-cfrmsub-frm-dv_cs_candidate_personal_info_FirstName'))
        WebDriverWait(driver, 10).until(element_present)
    except TimeoutException:
        print("Timed out waiting for page to load")

    time.sleep(random.randint(0, 2))

    printf(f"successfully made account for fake email {email}")


def application_part_1(driver, random_city, fake_identity):
    for key in XPATHS_2.keys():

        if((key == 'first_name') or ('perfered_first_name')):
            info = fake_identity['first_name']

        elif(key == 'last_name'):
            info = fake_identity['last_name']
        elif(key == 'zip'):
            info = CITIES_TO_ZIP_CODES[random_city][0]
        elif(key == 'pn'):
            info = random_phone(format=3)
        elif(key == 'work_experience_employer'):
            info = fake.company()
        elif(key == 'work_experinece_title'):
            info = fake.job()


        driver.find_element_by_xpath(XPATHS_2.get(key)).send_keys(info)

        # SELECT THE PLACE OF RESIDENCE
        select = Select(driver.find_element_by_id(REGION_COUNTRY))
        select.select_by_visible_text(COUNTRY)
        select = Select(driver.find_element_by_id(REGION_STATE))
        select.select_by_visible_text(STATE)
        select = Select(driver.find_element_by_id(REGION_CITY))
        select.select_by_visible_text(CITY)

        # SELECT EMPLOY HISTORY
        select = Select(driver.find_element_by_id(EMPLOY_HISTORY))
        select.select_by_visible_text(NO)

        # SELECT AVALIABLILITY
        select = Select(driver.find_element_by_id(WILLING_WORK_HOURS))
        select.select_by_value(str(random.randint(1, 5)))
        select = Select(driver.find_element_by_id(PREF_HOURS))
        select.select_by_value(str(random.randint(1, 5)))

        driver.find_element_by_xpath(XPATH_AVAL['hours_holi']).click()
        driver.find_element_by_xpath(XPATH_AVAL['hours_times']).click()
        driver.find_element_by_xpath(XPATH_AVAL['current_job']).click()


def application_part_2(driver, random_city, fake_identity):

    # make resume
    info = ''
    resume_filename = fake_identity['last_name']+'-Resume'
    make_resume(fake_identity['first_name']+' '+fake_identity['last_name'],
                fake_identity['email'], resume_filename+'.pdf')

    # Send Resume
    info = os.getcwd() + '/'+resume_filename+'.pdf'
    driver.find_element_by_xpath(UPLOAD_A_RESUME_BUTTON).send_keys(info)

    driver.find_element_by_xpath(ATTACH_RESUME).click()

    printf(f"successfully filled out app forms for {random_city}")

    # take out the trash
    os.remove(resume_filename+'.pdf')


def application_part_3(driver, random_city, fake_identity):
    for key in XPATH_QUALS.keys():

        driver.find_element_by_xpath(XPATH_QUALS.get(key)).click()


def application_part_4(driver, random_city, fake_identity):
    for key in XPATH_EEO.keys():
        driver.find_element_by_xpath(XPATH_EEO.get(key)).click()

    driver.find_element_by_xpath(random.choice(XPATH_RACES)).click()


def application_part_5(driver, random_city, fake_identity):
    for key in XPATH_VOL.keys():
        if key in ('VOL_NAME'):
            driver.find_element_by_xpath(XPATH_VOL.get(key)).send_keys(
                fake_identity['first_name'] + " " + fake_identity['last_name'])
        elif key in ('VOL_DATE'):
            driver.find_element_by_xpath(XPATH_VOL.get(
                key)).send_keys(today.strftime("%m/%d/%y"))
        elif key in ('VOL_no'):
            driver.find_element_by_xpath(XPATH_VOL.get(key)).click()


def application_part_6(driver, random_city, fake_identity):
    for key in XPATH_QUEST.keys():
        driver.find_element_by_xpath(XPATH_QUEST.get(key)).click()


def fill_out_application_and_submit(driver, random_city, fake_identity):

    application_part_1(driver, random_city, fake_identity)
    driver.find_element_by_xpath(CONTINUE).click()
    time.sleep(1)
    application_part_2(driver, random_city, fake_identity)
    driver.find_element_by_xpath(CONTINUE2).click()
    time.sleep(1)
    application_part_3(driver, random_city, fake_identity)
    time.sleep(1)
    driver.find_element_by_xpath(CONTINUE).click()
    application_part_4(driver, random_city, fake_identity)
    time.sleep(1)
    driver.find_element_by_xpath(CONTINUE).click()
    application_part_5(driver, random_city, fake_identity)
    time.sleep(1)
    driver.find_element_by_xpath(CONTINUE).click()
    time.sleep(1)
    driver.find_element_by_xpath(QUEST).click()
    time.sleep(2)

    try:
        element_present = expected_conditions.presence_of_element_located(
            (By.ID, 'SurveyControl_SurveySubmit'))
        WebDriverWait(driver, 10).until(element_present)
    except TimeoutException:
        print("Timed out waiting for page to load")

    application_part_6(driver, random_city, fake_identity)
    driver.find_element_by_xpath(QUEST_SUBMIT).click()

    try:
        element_present = expected_conditions.presence_of_element_located(
            (By.ID, 'et-ef-content-ftf-gp-j_id_id16pc9-page_0-eSignatureBlock-cfrmsub-frm-dv_cs_esignature_FullName'))
        WebDriverWait(driver, 10).until(element_present)
    except TimeoutException:
        print("Timed out waiting for page to load")

    driver.find_element_by_xpath(FULL_NAME).send_keys(
        fake_identity['first_name'] + " " + fake_identity['last_name'])

    driver.find_element_by_xpath(CONTINUE).click()
    time.sleep(1)
    driver.find_element_by_xpath(SUBMIT_APP).click()
    time.sleep(2)

    print("APPLICATION SENT")


def random_email(name=None):
    if name is None:
        name = fake.name()

    mailGens = [lambda fn, ln, *names: fn + ln,
                lambda fn, ln, *names: fn + "." + ln,
                lambda fn, ln, *names: fn + "_" + ln,
                lambda fn, ln, *names: fn[0] + "." + ln,
                lambda fn, ln, *names: fn[0] + "_" + ln,
                lambda fn, ln, *names: fn + ln +
                str(int(1 / random.random() ** 3)),
                lambda fn, ln, *names: fn + "." + ln +
                str(int(1 / random.random() ** 3)),
                lambda fn, ln, *names: fn + "_" + ln +
                str(int(1 / random.random() ** 3)),
                lambda fn, ln, *names: fn[0] + "." +
                ln + str(int(1 / random.random() ** 3)),
                lambda fn, ln, *names: fn[0] + "_" + ln + str(int(1 / random.random() ** 3)), ]

    emailChoices = [float(line[2]) for line in EMAIL_DATA]

    return random.choices(mailGens, MAIL_GENERATION_WEIGHTS)[0](*name.split(" ")).lower() + "@" + \
        random.choices(EMAIL_DATA, emailChoices)[0][1]


def main():
    
    while True:
        random_city = random.choice(list(CITIES_TO_URLS.keys()))
        try:
            driver = start_driver(random_city)
        except Exception as e:
            printf(f"FAILED TO START DRIVER: {e}")
            pass

        time.sleep(1)

        fake_first_name = fake.first_name()
        fake_last_name = fake.last_name()
        fake_email = random_email(fake_first_name+' '+fake_last_name)

        fake_identity = {
            'first_name': fake_first_name,
            'last_name': fake_last_name,
            'email': fake_email
        }

        try:
            generate_account(driver, fake_identity)
        except Exception as e:
            printf(f"FAILED TO CREATE ACCOUNT: {e}")
            pass

        try:
            fill_out_application_and_submit(driver, random_city, fake_identity)
        except Exception as e:
            printf(f"FAILED TO FILL OUT APPLICATION AND SUBMIT: {e}")
            pass
            driver.close()
            continue

        driver.close()


if __name__ == '__main__':
    main()
    sys.exit()
