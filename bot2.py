import json
import time
from pathlib import Path

from selenium import webdriver
from tools import install_webdriver, webdriver_executable, download_stealth_js

chrome_version = '95.0.4638.69'

install_webdriver(chrome_version)
download_stealth_js()


class CantFindElement(Exception):
    pass


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
        self.watch_list = {}
        self.cookie_path = Path().cwd() / 'cookie.json'

        # os.popen(str(chromium_executable()) + ' --remote-debugging-port=9222')
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('log-level=3')
        chrome_options.add_argument("--disable-popup-blocking")
        # chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        self.driver = webdriver.Chrome(executable_path=str(webdriver_executable(chrome_version)),
                                       options=chrome_options)
        with open('stealth.min.js') as f:
            js = f.read()
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": js
        })
        self.finish_count = 0

    def find_element_by_xpath(self, xpath, wait_time=60):
        for i in range(wait_time):
            try:
                return self.driver.find_element_by_xpath(xpath)
            except:
                time.sleep(1)
        else:
            raise CantFindElement(f'没有找到元素 {xpath}')

    def find_elements_by_css_selector(self, css_selector):
        for i in range(60):
            try:
                return self.driver.find_elements_by_css_selector(css_selector)
            except:
                time.sleep(1)
        else:
            raise CantFindElement(f'没有找到元素 {css_selector}')

    def save_cookie(self):
        with open(self.cookie_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.driver.get_cookies()))

    def load_cookie(self):
        if not self.cookie_path.is_file():
            return
        with open(self.cookie_path, 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
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
        self.driver.delete_all_cookies()
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

    def open_video_win(self, video_item: VideoElement):
        print(f'开始观看：{video_item.title}')
        last_open_windows = self.driver.window_handles
        video_item.click()
        self.watch_list[self.get_new_open_window(last_open_windows)] = {'title': video_item.title, 'not_load': 0}

    def check_finish(self, window):
        try:
            self.driver.switch_to.window(window)
            time.sleep(2)
            if self.find_element_by_xpath(
                    '//*[@id="video-box"]/div/xt-wrap/xt-controls/xt-inner/xt-playbutton/xt-tip',
                    wait_time=5).get_attribute('innerText') != '暂停':
                self.driver.execute_script('arguments[0].click()', self.find_element_by_xpath(
                    '//*[@id="video-box"]/div/xt-wrap/xt-controls/xt-inner/xt-playbutton'))
                time.sleep(2)
                if self.find_element_by_xpath(
                        '//*[@id="video-box"]/div/xt-wrap/xt-controls/xt-inner/xt-playbutton/xt-tip',
                        wait_time=5).get_attribute('innerText') != '暂停':
                    raise CantFindElement()
            if '100' in self.find_element_by_xpath(
                    '//*[@id="app"]/div[2]/div[2]/div[3]/div/div[2]/div/div/section[1]/div[2]/div/div/span',
                    wait_time=5).text:
                del self.watch_list[window]
                self.driver.close()
                self.finish_count += 1
                return True
            video_element = self.find_element_by_xpath('//*[@id="video-box"]/div/xt-wrap/video', wait_time=5)
            last_duration = video_element.get_attribute('currentTime')
            for i in range(3):
                time.sleep(5)
                if video_element.get_attribute('currentTime') != last_duration:
                    break
            else:
                raise CantFindElement()
            return False
        except CantFindElement:
            self.watch_list[window]['not_load'] += 1
            print(self.watch_list[window]['title'], '加载失败')
            return False
        except:
            return False

    def wait_watch(self):
        for window, item in self.watch_list.items():
            if self.check_finish(window):
                print(f'{self.finish_count} {item["title"]} finish')
                return
            else:
                if self.watch_list[window]['not_load'] >= 3:
                    self.watch_list[window]['not_load'] = 0
                    self.driver.refresh()
                    print(self.watch_list[window]['title'], ' 刷新')
            time.sleep(1)

    def get_new_open_window(self, last_windows):
        for item in self.driver.window_handles:
            if item not in last_windows:
                return item

    def run(self):
        if not self.login_by_cookie():
            self.driver.delete_all_cookies()
            self.login()
            self.wait_for_login()
        self.find_element_by_xpath('//*[@id="left_menu_ul"]/li[3]/a').click()
        self.driver.switch_to.alert.accept()
        input('回车开始')
        self.save_cookie()
        video_list = self.switch_video_list()
        list_window_handle = self.driver.current_window_handle
        while video_list:
            while len(self.watch_list) < 10 and video_list:
                item = video_list.pop(0)
                self.driver.switch_to.window(list_window_handle)
                self.open_video_win(item)
            self.wait_watch()


if __name__ == '__main__':
    bot = LearnBot2()
    bot.run()
