import os
import time
from pathlib import Path
from typing import List, Optional

import selenium
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

# from browser_helper.webdriver_dl import get_driver, get_chrome_version

# from browser_helper.webdriver_dl import get_driver
from driver_helper import DriverHelper


# execute_path = get_driver()

def now_time():
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())


class MyBrowser:
    def __init__(self, download_folder: Path = None, screenshot_dir: Path = None, header_less=False):
        self.chrome_opt = Options()
        prefs = {"profile.default_content_settings.popups": 0}
        if download_folder:
            prefs.update({"download.default_directory": str(download_folder)})
        self.chrome_opt.add_experimental_option('prefs', prefs)
        if header_less:
            self.chrome_opt.add_argument('--headless')
        self.driver: Optional[selenium.webdriver.Chrome] = None
        self.shoot_n = 0
        self.download_folder = download_folder
        self.screenshot_dir = screenshot_dir or (Path(os.getcwd()) / 'screenshot')

    def load_browser(self):
        # 根据浏览器版本加载浏览器
        driver_helper = DriverHelper()
        execute_path = driver_helper.get_driver()
        self.driver = webdriver.Chrome(service=Service(execute_path), options=self.chrome_opt)
        # self.driver.set_window_size(width=1920, height=1080)
        self.driver.maximize_window()

    def get(self, url):
        if not self.driver:
            self.load_browser()
        self.driver.get(url)

    def get_screenshot_as_file(self, file_path=None):
        if not self.screenshot_dir.is_dir():
            self.screenshot_dir.mkdir()
        png_file_path = self.screenshot_dir / (file_path or str(int(time.time())))
        print(f'saving {png_file_path}')
        self.driver.get_screenshot_as_file(str(png_file_path))
        return png_file_path

    def find_element(self, value, by=By.XPATH, timeout=10) -> WebElement:
        for i in range(timeout):
            try:
                return self.driver.find_element(by, value)
            except Exception as e:
                time.sleep(1)
        raise Exception(f'未找到 {by} {value}')

    def find_elements(self, value, by=By.CSS_SELECTOR) -> List[WebElement]:
        for i in range(10):
            try:
                return self.driver.find_elements(by, value)
            except Exception as e:
                time.sleep(1)
        raise Exception(f'未找到 {by} {value}')

    def click_element(self, value, by=By.XPATH, timeout=10, just_try=False):
        try:
            element = self.find_element(by=by, value=value, timeout=timeout)
            element.click()
        except Exception as e:
            if just_try:
                return
            else:
                raise e

    def hover_click(self, hover_by, hover_value, click_by, click_value):
        """
        悬停并点击
        """
        hover_element = self.find_element(by=hover_by, value=hover_value)
        action = ActionChains(self.driver).move_to_element(hover_element)
        # 对定位到的元素执行悬停操作
        action.perform()
        time.sleep(1)
        # 点击
        self.find_element(by=click_by, value=click_value).click()
        action.release()

    def check_download_file(self, file_name_filter, timeout=120):
        if not self.download_folder:
            raise Exception('not set download folder')
        for i in range(timeout):
            try:
                return list(self.download_folder.glob(file_name_filter))[0]
            except:
                time.sleep(1)
                continue
        self.get_screenshot_as_file(f'download_timeout_{time.time()}.png')
        raise Exception(f'下载超时 timeout={timeout}')

    def get_local_storage(self, key):
        return self.driver.execute_script("return window.localStorage.getItem(arguments[0]);", key)

    def set_local_storage(self, k, v):
        return self.driver.execute_script("return window.localStorage.setItem(arguments[0], arguments[1]);", k, v)

    def close(self):
        try:
            self.driver.close()
        except:
            pass

    def quit(self):
        try:
            self.driver.quit()
        except:
            pass
