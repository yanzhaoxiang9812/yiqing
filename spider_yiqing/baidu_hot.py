# -*- coding:utf-8 -*-

"""==============================
@author: 
@file: baidu_hot.py
@date: 2020-07-01
@time: 20:56:00
=============================="""
from selenium.webdriver import Chrome, ChromeOptions
import time
import yiiqing_data
import traceback

def get_baidu_hot():
    baidu_hot = "https://voice.baidu.com/act/newpneumonia/newpneumonia/?from=osari_pc_3#tab1"

    option = ChromeOptions() # 创建谷歌浏览器示例
    option.add_argument("--headless") # 加快爬取数据，不需要打开浏览器
    option.add_argument("--no-sandbox") # 部署linux

    browser = Chrome(r"C:\Program Files\Google\Chrome\Application\chromedriver.exe", options=option)
    browser.get(baidu_hot)
    print(browser)

    dl = browser.find_element_by_css_selector('#ptab-1 > div.Virus_1-1-306_2SKAfr > div.Common_1-1-306_3lDRV2 > span')
    dl.click()
    time.sleep(1)
    # 找到读热标签
    list = []
    for i in range(1, 21):
        c = browser.find_elements_by_xpath('//*[@id="ptab-1"]/div[3]/div/div[2]/a/div'.format(i))

        list.append(c)

    list1 = []
    for i in range(1, 21):
        for j in list[i-1]:
            context = j.text
            list1.append(context)
            print(list1)
    return list1

def update_hotsearch():
    cursor = None
    conn = None
    try:
        context = get_baidu_hot()
        print(f"{time.asctime()}开始更新热搜数据")
        conn, cursor = yiiqing_data.get_conn()
        sql = "insert into hotsearch(dt,content) values(%s,%s)"

        ts = time.strftime("%Y-%m-%d %X")
        for i in context:
            cursor.execute(sql, (ts, i))
        conn.commit()
        print(f"{time.asctime()}数据更新完毕")
    except:
        traceback.print_exc()
    finally:
        yiiqing_data.close_conn(conn, cursor)


if __name__ == '__main__':
    get_baidu_hot()
    # update_hotsearch()
