# 学堂在线  自动学习
import json
import time
from pathlib import Path

from selenium.webdriver.common.by import By

from base import MyBrowser
from driver_helper import DriverHelper

driver_helper = DriverHelper()
execute_path = driver_helper.get_driver()


class CantFindElement(Exception):
    pass


class VideoElementItem:
    def __init__(self, element):
        self.title = element.find_element('xpath', './/span').text
        self.url = element.find_element('xpath', './div[2]/div')
        self.finish_status = True if element.find_element('xpath', './div[2]/div').text == '已完成' else False

    def open(self):
        self.url.click()


class LearnBot2(MyBrowser):
    def __init__(self, username=None, password=None):
        super(LearnBot2, self).__init__()
        self.windows_limit = 5
        self.username = username
        self.password = password
        self.watch_list = {}
        self.cookie_path = Path().cwd() / 'cookie.json'

        # os.popen(str(chromium_executable()) + ' --remote-debugging-port=9222')
        self.chrome_opt.add_argument('log-level=3')
        self.chrome_opt.add_argument("--disable-popup-blocking")
        self.chrome_opt.add_argument("--mute-audio")
        # chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        self.load_browser()

        with open('stealth.min.js') as f:
            js = f.read()
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": js
        })
        self.finish_count = 0

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
        self.get('https://student.uestcedu.com/console')
        self.driver.delete_all_cookies()
        self.load_cookie()
        self.driver.get('https://student.uestcedu.com/console')
        return self.wait_for_login(10)

    def login(self):
        self.driver.get('https://student.uestcedu.com/console/')
        if self.username and self.password:
            self.find_element('//*[@id="txtLoginName"]').send_keys(self.username)
            self.find_element('//*[@id="txtPassword"]').send_keys(self.password)
            self.find_element('//*[@id="verify_button"]').click()
            self.driver.switch_to.alert.accept()
            # msm_code = input('验证码:')
            # self.find_element_by_xpath('//*[@id="txtSmsCode"]').send_keys(msm_code)
            # self.find_element_by_xpath('//*[@id="login_button"]').click()
        else:
            self.find_element('/html/body/div/div/div/div/div/ul/li[2]').click()

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

    def parse_video_list(self):
        print('开始解析列表...')
        handles = self.driver.window_handles
        for handle in handles:
            self.driver.switch_to.window(handle)
            if '内容总览' in self.driver.page_source:
                print('找到内容列表')
                elements_list = self.find_elements('.leaf-detail')
                video_element_list = []
                finish_count = 0
                not_finish_count = 0
                for element in elements_list:
                    if 'iconfont icon--shipin' == element.find_element(By.XPATH, './/i').get_attribute('class'):
                        video_item = VideoElementItem(element)
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

    def start_video(self, video_item: VideoElementItem):
        print(f'开始观看：{video_item.title}')
        last_open_windows = self.driver.window_handles
        video_item.open()
        new_window = self.get_new_open_window(last_open_windows)

        # videoArea = self.driver.find_element(By.XPATH, '//*[@id="video-box"]')  # 视频播放区域
        # ActionChains(self.driver).move_to_element(videoArea).perform()  # 鼠标悬停
        # speedBox = self.driver.find_element(By.XPATH, '//*[@id="video-box"]/div/xt-wrap/xt-controls/xt-inner/xt-speedbutton')  # 视频倍速按钮
        # ActionChains(self.driver).move_to_element(speedBox).perform()  # 鼠标悬停
        # self.driver.find_element(By.XPATH, '//*[@id="video-box"]/div/xt-wrap/xt-controls/xt-inner/xt-speedbutton/xt-speedlist/ul/li[1]').click()  # 视频1.5倍速

        self.watch_list[new_window] = {'title': video_item.title, 'not_load': 0}

    def check_finish(self, window, item):
        try:
            self.driver.switch_to.window(window)
            time.sleep(2)
            if self.find_element(
                    '//*[@id="video-box"]/div/xt-wrap/xt-controls/xt-inner/xt-playbutton/xt-tip').get_attribute(
                'innerText') != '暂停':
                self.driver.execute_script('arguments[0].click()', self.find_element(
                    '//*[@id="video-box"]/div/xt-wrap/xt-controls/xt-inner/xt-playbutton'))
                time.sleep(2)
                if self.find_element(
                        '//*[@id="video-box"]/div/xt-wrap/xt-controls/xt-inner/xt-playbutton/xt-tip').get_attribute(
                    'innerText') != '暂停':
                    raise CantFindElement()
            if '100' in self.find_element(
                    '//*[@id="app"]/div[2]/div[2]/div[3]/div/div[2]/div/div/section[1]/div[2]/div/div/span').text:
                del self.watch_list[window]
                self.driver.close()
                self.finish_count += 1
                print(f'### {item["title"]} -- 完成 ###')
                return True
            video_element = self.find_element('//*[@id="video-box"]/div/xt-wrap/video', timeout=5)
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
            if self.check_finish(window, item):
                print(f'{self.finish_count} {item["title"]} finish')
                return
            else:
                if self.watch_list[window]['not_load'] >= 3:
                    self.watch_list[window]['not_load'] = 0
                    self.driver.refresh()
                    print(self.watch_list[window]['title'], ' 刷新')
            time.sleep(2)

    def get_new_open_window(self, last_windows):
        for item in self.driver.window_handles:
            if item not in last_windows:
                return item

    def run(self):
        if not self.login_by_cookie():
            self.driver.delete_all_cookies()
            self.login()
            self.wait_for_login()
        self.save_cookie()

        self.find_element('//*[@id="left_menu_ul"]/li[3]/a').click()
        self.driver.switch_to.alert.accept()
        while True:
            input('回车开始')
            self.watch_list = {}
            video_list = self.parse_video_list()
            list_window_handle = self.driver.current_window_handle
            while video_list:
                while len(self.watch_list) < self.windows_limit and video_list:
                    item = video_list.pop(0)
                    self.driver.switch_to.window(list_window_handle)
                    self.start_video(item)
                self.wait_watch()


if __name__ == '__main__':
    bot = LearnBot2()
    bot.run()
