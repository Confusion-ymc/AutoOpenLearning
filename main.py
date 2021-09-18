import datetime
import os
import time
import traceback

from selenium import webdriver
from tools import install_browser, install_webdriver, webdriver_executable, chromium_executable

install_browser()
install_webdriver()
os.popen(str(chromium_executable()) + ' --remote-debugging-port=9222')


class LearnBot:
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('log-level=3')
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        self.driver = webdriver.Chrome(executable_path=str(webdriver_executable()), options=chrome_options)

        self.count = 0
        self.driver.get('https://student.uestcedu.com/console/')

    def login(self, username, password):
        while True:
            self.driver.get('https://student.uestcedu.com/console/')
            self.driver.find_element_by_xpath('//*[@id="txtLoginName"]').send_keys(username)
            self.driver.find_element_by_xpath('//*[@id="txtPassword"]').send_keys(password)
            self.driver.find_element_by_xpath('//*[@id="verify_button"]').click()
            self.driver.switch_to.alert.accept()
            msm_code = input('验证码:')
            self.driver.find_element_by_xpath('//*[@id="txtSmsCode"]').send_keys(msm_code)
            self.driver.find_element_by_xpath('//*[@id="login_button"]').click()
            time.sleep(5)
            if 'https://student.uestcedu.com/console/main.html?' in self.driver.current_url:
                break

    def qr_login(self):
        self.driver.find_element_by_xpath('/html/body/div/div/div/div/div/ul/li[2]').click()

    def run(self):
        while True:
            try:
                choice = input('选择你要的操作，(默认)1.开始刷课，2.退出程序\n1):Run... \n2):Quit\n')
                if not choice or choice == '1':
                    pass
                elif choice == '2':
                    break
                else:
                    continue
                handles = self.driver.window_handles
                self.driver.switch_to.window(handles[-1])
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(self.driver.find_element_by_xpath('/html/body/table/tbody/tr[2]/td/iframe'))
                self.driver.switch_to.frame(self.driver.find_element_by_xpath('//*[@id="w_code"]'))
                self.expand_all()
                time.sleep(2)
                node_list = self.find_not_finish()
                self.play(node_list)
                print('全部完成...')
            except Exception as e:
                traceback.print_exc()

    def play(self, a_list):
        for i, a in enumerate(a_list):
            a.click()
            time.sleep(5)
            title = a.text
            print(f'开始学习 {title}')
            self.wait_finish()
            self.count += 1
            print(f'{self.count} {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {title} 学习完成')

    def expand_all(self):
        """
        展开所有加号
        :return:
        """
        for i in self.driver.find_elements_by_css_selector("img[src='/_web_api/images/treeicon/plusnode.gif']"):
            try:
                i.click()
            except Exception as e:
                # traceback.print_exc()
                pass
        for i in self.driver.find_elements_by_css_selector("img[src='/_web_api/images/treeicon/cornerplusnode.gif']"):
            try:
                i.click()
            except Exception as e:
                # traceback.print_exc()
                pass

    def find_not_finish(self):
        """
        查找待学习的标签
        :return:
        """
        # 未开始
        not_attempt_list = self.driver.find_elements_by_css_selector("span.scorm.notattempt")
        # 未完成
        incomplete = self.driver.find_elements_by_css_selector("span.scorm.incomplete")
        return [i.find_element_by_xpath('../a') for i in (incomplete + not_attempt_list)]

    def wait_finish(self):
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(self.driver.find_element_by_xpath('/html/body/table/tbody/tr[2]/td/iframe'))
        self.driver.switch_to.frame(self.driver.find_element_by_xpath('//*[@id="w_lms_content"]'))
        wait_count = 0
        while wait_count <= 60 * 60:
            if '您正在学习' in self.driver.find_elements_by_xpath('//td')[-1].text:
                time.sleep(5)
                wait_count += 5
            else:
                break
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(self.driver.find_element_by_xpath('/html/body/table/tbody/tr[2]/td/iframe'))
        self.driver.switch_to.frame(self.driver.find_element_by_xpath('//*[@id="w_code"]'))

    def stop(self):
        try:
            self.driver.quit()
        except:
            pass
        print('正常退出')


if __name__ == '__main__':
    learn_bot = LearnBot()
    learn_bot.qr_login()
    learn_bot.run()
    learn_bot.stop()
