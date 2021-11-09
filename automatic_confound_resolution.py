import requests
import numpy as np
from typing import List
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time


class SharedData:
    dummy_skill_url: str = "<YOUR_DUMMY_SKILL_URL>"
    wait: int = 10
    wait_per_skill: int = 2
    username: str = "<YOUR_USERNAME>"
    password: str = "<YOUR_PASSWORD>"
    skills_page: str = "https://www.amazon.com/gp/skills/your-skills"
    skill_link_prefix: str = "https://www.amazon.com/gp/product/"


def login():
    driver = webdriver.Chrome()

    # Open skill page
    driver.get(SharedData.dummy_skill_url)

    # Login page will pop up: sign in

    # # Enter email ID
    email_field = driver.find_element(By.ID,
                                      "ap_email"
                                      )
    email_field.send_keys(SharedData.username)

    # Enter password
    password_field = driver.find_element(By.ID,
                                         "ap_password"
                                         )
    password_field.send_keys(SharedData.password)
    password_field.send_keys(Keys.RETURN)

    return driver


def try_out_utterance(driver, utterance: str):
    # Open skill page
    driver.get(SharedData.dummy_skill_url)

    # Find input field
    input_text_field = driver.find_element(By.CLASS_NAME,
                                           "askt-utterance__input")

    # Enter utterance
    input_text_field.send_keys(utterance)

    # Press Enter
    input_text_field.send_keys(Keys.RETURN)

    # Wait for a few seconds (to make sure it went through)
    time.sleep(SharedData.wait)

    # Look for "disabled in the past" message
    response = driver.find_element(
        By.CLASS_NAME, "askt-dialog__message--active-response")
    if "sorry i couldn't understand" in response.get_attribute('innerText').lower():
        # Alexa is unsure which one to trigger, go with suggestion
        input_text_field.send_keys("try it")
        input_text_field.send_keys(Keys.RETURN)

        # Wait for a few seconds (to make sure it went through)
        time.sleep(SharedData.wait)
    
    # Update Alexa's response
    response = driver.find_element(
        By.CLASS_NAME, "askt-dialog__message--active-response")

    # May have disabled in the past; allow re-enabling
    if 'do you want to enable it again' in response.get_attribute('innerText').lower():
        # Type out "yes" and respond
        input_text_field.send_keys("yes")
        input_text_field.send_keys(Keys.RETURN)

        # Wait for a few seconds (to make sure it went through)
        time.sleep(SharedData.wait)
    
    # Update Alexa's response
    response = driver.find_element(
        By.CLASS_NAME, "askt-dialog__message--active-response")
    
    # Skill may have adult content
    if 'do you want to continue' in response.get_attribute('innerText').lower() or 'would you like to continue' in response.get_attribute('innerText').lower():
        # Type out "yes" and respond
        input_text_field.send_keys("yes")
        input_text_field.send_keys(Keys.RETURN)

        # Wait for a few seconds (to make sure it went through)
        time.sleep(SharedData.wait)


def try_out_utterances(driver, utterances: List[str]):
    for utterance in utterances:
        try_out_utterance(driver, utterance)


def check_skills_active(driver):
    # Take driver page to skills page
    driver.get(SharedData.skills_page)

    # Get list of skills listed on page
    skills = driver.find_elements(
        By.CLASS_NAME, "a2s-asin-details")

    ids = []
    for skill in skills:
        child = skill.find_element(By.CLASS_NAME, "a-link-normal")
        link = child.get_attribute("href")
        # Extract skill ID
        id = link.split("/")[-1].split("?")[0]
        ids.append(id)
    return ids


def check_skills_status(driver, skill_ids: List[str], disable: bool=False):
    status = []

    for skill_id in skill_ids:
        # Take driver page to skills page
        driver.get(SharedData.skill_link_prefix + skill_id)

        # Find relevant button
        disable_button = driver.find_element(
            By.ID, "a2s-skill-disable-button")

        # Skill is enabled- disable it
        if "aok-hidden" not in disable_button.get_attribute('class').split():
            status.append(True)

            if disable:

                # Find disable button
                click_button = disable_button.find_element(
                    By.CLASS_NAME, "a-button-input")
                click_button.click()

                # Find modal (popup)
                modal = driver.find_element(By.CLASS_NAME, 'a-popover-modal')

                # Find Disable Skill (second) button
                disable_span = modal.find_element(
                    By.CLASS_NAME, 'a-button-primary')
                disable_button = disable_span.find_element(
                    By.CLASS_NAME, 'a-button-input')

                # Wait for 1-2 seconds (let JS import)
                time.sleep(SharedData.wait_per_skill)

                # Disable skill
                disable_button.click()

                # Wait a bit
                time.sleep(SharedData.wait)
        else:
            status.append(False)
    return np.array(status)


def disable_skill(skill_id: str):
    post_data = {

    }
    r = requests.delete(SharedData.url +
                        f"/v1/users/~current/skills/{skill_id}/enablement",
                        headers={
                            'Authorization': SharedData.token,
                            'Content-Type': 'application/json'
                        },
                        data=post_data)
    return (r.status_code == 204)


def disable_skills(skill_ids: List[str]):
    statuses = []
    for skill_id in skill_ids:
        statuses.append(disable_skill(skill_id))
    return np.all(statuses)


def which_skill_enabled(driver, utterance, skill_ids):
    # Make sure relevant skills are disabled
    check_skills_status(driver, skill_ids, disable=True)

    # Try out utterance
    try_out_utterance(driver, utterance)

    # See which skill was enabled
    status = check_skills_status(driver, skill_ids)

    if np.sum(status) == 0:
        raise ValueError("None of these skills were activated")

    # Return relevant skill
    return skill_ids[np.nonzero(status)[0][0]]


if __name__ == "__main__":
    # skill_simulation_api("alexa start counting sheep")
    # check_if_skill_active("B07FK56GVY")

    # Get logged-in session
    driver = login()

    # Wait a bit (to make sure it went through)
    time.sleep(SharedData.wait)

    enabled = which_skill_enabled(
        driver,
        "alexa open joke of the day",
        ['B07L961W9V', 'B07D3M6MD4', 'B07K6GTD9M', 'B07LFBVCB1', 'B08BL7Y8L5', 'B07LFC8BJQ'])

    print("Skill triggered:", enabled)
    driver.quit()
