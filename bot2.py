import json
import os
import pickle
import time
from pathlib import Path

from selenium import webdriver
from tools import install_browser, install_webdriver, webdriver_executable, chromium_executable, download_stealth_js

install_browser()
install_webdriver()
exit()
download_stealth_js()


class VideoElement:
    def __init__(self, element):
        self.title = element.find_element_by_xpath('.//span').text
        self.url = element.find_element_by_xpath('./div[2]/div')
        self.finish_status = True if element.find_element_by_xpath('./div[2]/div').text == '已完成' else False

    def click(self):
        self.url.click()


class LearnBot2:
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        # os.popen(str(chromium_executable()) + ' --remote-debugging-port=9222')
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('log-level=3')
        chrome_options.add_argument("--disable-popup-blocking")
        # chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        self.driver = webdriver.Chrome(executable_path=str(webdriver_executable()), options=chrome_options)
        with open('stealth.min.js') as f:
            js = f.read()
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": js
        })
        self.count = 0

    def find_element_by_xpath(self, xpath):
        for i in range(60):
            try:
                return self.driver.find_element_by_xpath(xpath)
            except:
                time.sleep(1)
        else:
            raise Exception(f'没有找到元素 {xpath}')

    def find_elements_by_css_selector(self, css_selector):
        for i in range(60):
            try:
                return self.driver.find_elements_by_css_selector(css_selector)
            except:
                time.sleep(1)
        else:
            raise Exception(f'没有找到元素 {css_selector}')

    def save_cookie(self):
        # data = self.driver.get_cookies()
        # with open('cookie.json', 'w') as f:
        #     json.dump(data, f)
        pickle.dump(self.driver.get_cookies(), open("cookie.pk1", 'wb'))

    def load_cookie(self):
        if not (Path().cwd() / 'cookie.json').is_file():
            return
        with open('cookie.json', 'r') as f:
            data = json.load(f)
        self.driver.delete_all_cookies()
        for cookie in data:
            self.driver.add_cookie({
                'domain': cookie['domain'],
                'name': cookie['name'],
                'value': cookie['value'],
                'path': cookie['path'],
                'expires': "",
                'httpOnly': False,
                'secure': False
            })

    def login_by_cookie(self):
        self.driver.get('https://student.uestcedu.com/console')
        self.load_cookie()
        self.driver.get('https://student.uestcedu.com/console')
        return self.wait_for_login(10)

    def login(self):
        self.driver.get('https://student.uestcedu.com/console/')
        if self.username and self.password:
            self.find_element_by_xpath('//*[@id="txtLoginName"]').send_keys(self.username)
            self.find_element_by_xpath('//*[@id="txtPassword"]').send_keys(self.password)
            self.find_element_by_xpath('//*[@id="verify_button"]').click()
            self.driver.switch_to.alert.accept()
            # msm_code = input('验证码:')
            # self.find_element_by_xpath('//*[@id="txtSmsCode"]').send_keys(msm_code)
            # self.find_element_by_xpath('//*[@id="login_button"]').click()
        else:
            self.find_element_by_xpath('/html/body/div/div/div/div/div/ul/li[2]').click()

    def wait_for_login(self, wait_time=None):
        if wait_time is None:
            forever = True
        else:
            forever = False
        n = 0
        while True:
            n += 1
            try:
                if 'https://student.uestcedu.com/console/main.html' in self.driver.current_url:
                    break
            except:
                pass
            if not forever and n == wait_time:
                print('login fail!')
                return False
            time.sleep(1)
        print('login success!')
        return True

    def switch_video_list(self):
        handles = self.driver.window_handles
        for handle in handles:
            self.driver.switch_to.window(handle)
            if '内容总览' in self.driver.page_source:
                print('找到内容列表')
                elements_list = self.find_elements_by_css_selector('.leaf-detail')
                video_element_list = []
                finish_count = 0
                not_finish_count = 0
                print('解析列表...')
                for element in elements_list:
                    if 'iconfont icon--shipin' == element.find_element_by_xpath('.//i').get_attribute('class'):
                        video_item = VideoElement(element)
                        if video_item.finish_status:
                            finish_count += 1
                        else:
                            not_finish_count += 1
                            video_element_list.append(video_item)
                print(
                    f'共找到内容 {len(elements_list)}\n视频内容{len(video_element_list)}\n已完成{finish_count}\n未完成{not_finish_count}')
                return video_element_list
        print('未找到内容列表！')
        return []

    def watch_video(self, video_item: VideoElement):
        print(f'开始观看：{video_item.title}')
        video_item.click()
        for window in self.driver.window_handles:
            self.driver.switch_to.window(window)
            if 'video' in self.driver.current_url:
                break
        time.sleep(5)
        self.driver.execute_script("arguments[0].setAttribute('class','xt_video_player_common_active')",
                                   self.find_element_by_xpath('//*[@id="video-box"]/div/xt-wrap/xt-controls/xt-inner/xt-speedbutton/xt-speedlist/ul/li[1]'))
        self.driver.execute_script("arguments[0].setAttribute('class','')",
                                   self.find_element_by_xpath(
                                       '//*[@id="video-box"]/div/xt-wrap/xt-controls/xt-inner/xt-speedbutton/xt-speedlist/ul/li[4]'))

        video_element = self.driver.find_element_by_xpath('//*[@id="video-box"]/div/xt-wrap/video')
        while video_element.get_attribute('duration') != video_element.get_attribute('currentTime'):
            time.sleep(1)
        print('finish')
        self.driver.close()

    def run(self):
        if not self.login_by_cookie():
            self.login()
            self.wait_for_login()
        self.find_element_by_xpath('//*[@id="left_menu_ul"]/li[3]/a').click()
        self.driver.switch_to.alert.accept()
        input('回车开始')
        self.save_cookie()
        video_list = self.switch_video_list()
        list_window_handle = self.driver.current_window_handle
        for item in video_list:
            self.driver.switch_to.window(list_window_handle)
            self.watch_video(item)


if __name__ == '__main__':
    bot = LearnBot2()
    bot.run()
