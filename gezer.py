import base64
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import os
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
            ID = lines[2].strip()
            id.send_keys(lines[2].strip())
    except FileNotFoundError:
        username.send_keys(input("Enter username: "))
        password.send_keys(input("Enter password: "))
        ID = int(input("Enter id: "))
        id.send_keys(str(ID))

    # click submit
    submit = driver.find_element(By.NAME, "ok")
    submit.click()
    go_to_download(driver, path, before, ID)
    
def go_to_download(driver, path, before, ID):
    try:
        # get the list of the course and print it
        courses_set = []
        for j in range(2, 20):
            try:
                for i in range(2, 20):
                    semster = driver.find_element(By.XPATH, f"/html/body/form[{j}]/table/caption/span").text
                    semster = semster[-2:-1]
                    number = driver.find_element(By.XPATH, f"/html/body/form[{j}]/table/tbody/tr[{i}]/th/span").text
                    name = driver.find_element(By.XPATH, f"/html/body/form[{j}]/table/tbody/tr[{i}]/td[1]/span").text
                    preiod = driver.find_element(By.XPATH, f"/html/body/form[{j}]/table/tbody/tr[{i}]/td[3]/span").text
                    date = driver.find_element(By.XPATH, f"/html/body/form[{j}]/table/tbody/tr[{i}]/td[4]/span").text
                    year = driver.find_element(By.XPATH, f"/html/body/form[{j}]/table/tbody/tr[{i}]/td[5]/span").text
                    year = year[-4:]
                    try:
                        scaned = driver.find_element(By.XPATH, f"/html/body/form[{j}]/table/tbody/tr[{i}]/td[6]/input").get_attribute("value")
                    except NoSuchElementException:
                        scaned = driver.find_element(By.XPATH, f"/html/body/form[{j}]/table/tbody/tr[{i}]/td[6]/span").text
                    # flip the name string
                    if "המחברת טרם נסרקה" == scaned or scaned == "הבחינה טרם התקיימה":
                        continue
                    name = name[::-1]
                    if date == "מיוחד":
                        date = "ג'" 
                    date = date[::-1]
                    scaned = scaned[::-1]
                    # add the 3 as tuple
                    courses_set.append((date, name, number, scaned, year, preiod, semster))
            except NoSuchElementException as e:
                pass
        print("Courses:")
        max_date_len = max([len(course[0]) for course in courses_set])
        max_name_len = max([len(course[1]) for course in courses_set])
        max_course_len = max([len(course[2]) for course in courses_set])
        max_scaned_len = max([len(course[3]) for course in courses_set])
        for i in range(len(courses_set)):
            if i < 9:
                print(f"[{i+1}] ", end=" ")
            else:
                print(f"[{i+1}]", end=" ")
            date_str = courses_set[i][0]
            name_str = str(courses_set[i][1])
            course_str = str(courses_set[i][2])
            scaned_str = str(courses_set[i][3])
            # if len is odd add space at the end
            if len(date_str) % 2 != 0:
                date_str += " "
            if len(name_str) % 2 != 0:
                name_str += " "
            if len(course_str) % 2 != 0:
                course_str += " "
            if len(scaned_str) % 2 != 0:
                scaned_str += " "
            date_padding = (max_date_len - len(date_str)) // 2
            name_padding = (max_name_len - len(name_str)) // 2
            course_padding = (max_course_len - len(course_str)) // 2
            scaned_padding = (max_scaned_len - len(scaned_str)) // 2
            

            print("||", " "*date_padding + date_str + " "*date_padding, "||", " "*name_padding + name_str + " "*name_padding, "||",
                   " "*course_padding + course_str + " "*course_padding, "||", " "*scaned_padding + scaned_str + " "*scaned_padding, "||")
        try:
            course = int(input("\nEnter the number of the course you want to download: (-1 to previous courses, 0 to exit) "))
        except KeyboardInterrupt:
            driver.quit()
            return
        if course == 0:
            try:
                driver.quit()
            except:
                pass
            return
        elif course == -1:
            # click on previous courses
            button = driver.find_element(By.XPATH, "/html/body/a[1]/span")
            button.click()
            go_to_download(driver, path, before, ID)
            return 
        course_to_change = courses_set[course-1]
        # look for button with value "קובץ המחברת" and edit its name and then click it
        button = driver.find_element(By.XPATH, "//input[@value='קובץ המחברת']")
        button.click()
        return change_and_download(driver, path, before, course_to_change, ID)
    except NoSuchElementException:
        print("Wrong username or password, please try again")
        driver.quit()
        set_up()
    

def change_and_download(driver, path, before, course_to_change, ID):
    # find toopen:2:1 name button
    button = driver.find_element(By.NAME, "expars")
    old_val = button.get_attribute("value")

    # decode old_val from base64
    decoded_bytes = base64.b64decode(old_val)
    # convert bytes to string
    new_string = decoded_bytes.decode('utf-8')

    type1 = ""
    type3 = "1"
    semster = course_to_change[6]
    if semster == "א":
        semster = ":1:0:"
        type1 = "1:"
    elif semster == "ב":
        semster = ":2:0:"
        type1 = "2:"
    elif semster == "י":
        semster = ":3:0:"
        type1 = "4:"
    
    prieod = course_to_change[5]
    if 'ה' in prieod:
        type1 = "4:"
        type3 = "3"

    date = course_to_change[0]
    if 'א' in date:
        type2 = "1"
    elif '1' in date:
        type2 = "11"
    elif '2' in date:
        type2 = "12"
    elif 'ב' in date:
        type2 = "2"
    elif 'ג' in date:
        type2 = "3"
      
    # ID : Year : Semester : 0 : type : Course Number : Course Date : type2
    new_string = ID + ":" + course_to_change[4] + semster + type1 + course_to_change[2] + ":" + type3 + ":" + type2

    # encode the string to base64
    encoded = base64.b64encode(new_string.encode('utf-8')).decode('utf-8') 
    # change the name of the button
    driver.execute_script(f"arguments[0].setAttribute('value', '{encoded}')", button)

    button = driver.find_element(By.NAME, "toopen:2:1")
    button.click()
    print(f"Downloading {course_to_change[1]} דעומ {course_to_change[0]} ...")
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