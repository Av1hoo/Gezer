import base64
import subprocess
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import os
import threading
from selenium.common.exceptions import NoSuchElementException

def set_up():
    # get from config file the path to download the file to
    default_config = False
    try:
        with open("config.txt", "r") as f:
            lines = f.readlines()
            if len(lines) != 4:
                print("Config file is not in the right format")
                raise FileNotFoundError
            # if config file is the deafult delete it to not use the default config
            if lines[0].strip() == "Username" or lines[1].strip() == "Password" or lines[2].strip() == "ID" or lines[3].strip() == "path\\path":
                default_config = True
                print("Default config file detected, please enter your details manually")
                raise FileNotFoundError
            else:
                path = lines[3].strip() 
    except FileNotFoundError:
        path = input("Enter the path to download the file to (Enter for 'Downloads' folder): ")
        if path == "":
            path = os.path.expanduser("~") + "\\Downloads"

    before = len(os.listdir(path))

    # Create a new instance of the Firefox driver
    options = Options()
    options.add_argument('-headless')
    # set the path to download the file to path
    options.set_preference("browser.download.dir", path)
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream")

    driver = webdriver.Firefox(options=options)
    login(driver, default_config, path, before)

def login(driver, default_config, path, before):
    driver.get("https://gezer1.bgu.ac.il/meser/login.php")
    # login
    username = driver.find_element(By.NAME, "username")
    password = driver.find_element(By.NAME, "pass")
    id = driver.find_element(By.NAME, "id")
    # if there is config file with the username and password, read it
    try:
        if default_config:
            raise FileNotFoundError
        with open("config.txt", "r") as f:
            lines = f.readlines()
            username.send_keys(lines[0].strip())
            password.send_keys(lines[1].strip())
            id.send_keys(lines[2].strip())
    except FileNotFoundError:
        username.send_keys(input("Enter username: "))
        password.send_keys(input("Enter password: "))
        id.send_keys(int(input("Enter id: ")))

    # click submit
    submit = driver.find_element(By.NAME, "ok")
    submit.click()
    go_to_download(driver, path, before)
    
def go_to_download(driver, path, before):
    try:
        # look for button with value "קובץ המחברת" and edit its name and then click it
        button = driver.find_element(By.XPATH, "//input[@value='קובץ המחברת']")
        button.click()
        change_and_download(driver, path, before)
    except NoSuchElementException:
        print("Wrong username or password, please try again")
        driver.quit()
        set_up()
    

def change_and_download(driver, path, before):
    # find toopen:2:1 name button
    button = driver.find_element(By.NAME, "expars")
    old_val = button.get_attribute("value")

    # decode old_val from base64
    decoded_bytes = base64.b64decode(old_val)

    # convert bytes to string
    new_string = decoded_bytes.decode('utf-8')
    new_string = new_string[0:-12] + input("New course number: ") + new_string[-4:]
    # encode the string to base64
    encoded = base64.b64encode(new_string.encode('utf-8')).decode('utf-8') 

    # change the name of the button
    driver.execute_script(f"arguments[0].setAttribute('value', '{encoded}')", button)

    button = driver.find_element(By.NAME, "toopen:2:1")
    button.click()
    print("Downloading...")
    check_if_downloaded(driver, path, before)

def check_if_downloaded(driver, path, before):
    after = len(os.listdir(path))
    while after == before:
        after = len(os.listdir(path))
    # Wait for download thread to finish
    driver.quit()
    print("Done")
    # get the latest downloaded file
    latest_file = max([os.path.join(path, f) for f in os.listdir(path)], key=os.path.getctime)
    # open the folder with the latest downloaded file selected
    subprocess.run(f'explorer /select,"{latest_file}"')

if __name__ == "__main__":
    set_up()