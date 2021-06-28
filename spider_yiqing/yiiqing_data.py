# -*- coding:utf-8 -*-
"""==============================
@author: 
@file: yiiqing_data.py
@date: 2020-06-30
@time: 18:16:22
=============================="""
import urllib.request as rq
import pymysql
from bs4 import BeautifulSoup
import json
import time
import traceback


url_today = "https://view.inews.qq.com/g2/getOnsInfo?name=disease_h5"
url_last = "https://view.inews.qq.com/g2/getOnsInfo?name=disease_other"
def gethtml(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36"}
    req = rq.Request(url, headers=headers)
    res = rq.urlopen(req)

    html = res.read().decode("utf-8")
    return html

def  get_history(url_last, url_today):

    # 历史数据
    html_last = gethtml(url_last)
    data_last = json.loads(html_last)
    #dict_keys(['chinaDayList', 'chinaDayAddList', 'dailyNewAddHistory', 'dailyHistory', 'wuhanDayList', 'articleList', 'provinceCompare', 'cityStatis', 'nowConfirmStatis'])
    data_last = json.loads(data_last["data"])

    # 当天数据
    html_today = gethtml(url_today)
    data_today = json.loads(html_today)
    # dict_keys(['lastUpdateTime', 'chinaTotal', 'chinaAdd', 'isShowAdd', 'showAddSwitch', 'areaTree'])
    data_today = json.loads(data_today["data"])
    # print(data_today.keys())

    history_data = {}
    for every_data in data_last["chinaDayList"]:
        date = "2020." + every_data["date"]
        tup = time.strptime(date, "%Y.%m.%d")
        date = time.strftime("%Y-%m-%d", tup)  # 改变时间格式,不然插入数据库会报错，数据库是datetime类型

        confirm = every_data["confirm"]
        suspect = every_data["suspect"]
        dead = every_data["dead"]
        heal = every_data["heal"]
        # nowConfirm = every_data["nowConfirm"]

        history_data[date] = {"confirm":confirm, "suspect":suspect, "dead":dead, "heal":heal}

    for every_data_add in data_last["chinaDayAddList"]:
        date_add = "2020." + every_data_add["date"]
        tup_add = time.strptime(date_add, "%Y.%m.%d")
        date_add = time.strftime("%Y-%m-%d", tup_add)  # 改变时间格式,不然插入数据库会报错，数据库是datetime类型

        confirm_add = every_data_add["confirm"]
        suspect_add = every_data_add["suspect"]
        dead_add = every_data_add["dead"]
        heal_add = every_data_add["heal"]
        # g更新，update函数可以添加新的键值对
        history_data[date_add].update({"confirm_add":confirm_add, "suspect_add":suspect_add, "dead_add":dead_add, "heal_add":heal_add})

    ''' areaTree ：name 中国数据
                   today
                   total
                   children :-name 省级数据 
                            -today
                            -total
                            -children:-name 市级数据
                                      -today
                                      -total
                            '''
    details = []
    update_time = data_today["lastUpdateTime"]
    data_country = data_today["areaTree"]
    # print(data_country[0]["children"])
    data_province = data_country[0]["children"]
    # print(data_province)
    for pro_infos in data_province:
        province = pro_infos["name"]
        for city_infos in pro_infos["children"]:
            city = city_infos["name"]
            confirm = city_infos["total"]["confirm"]
            confirm_add = city_infos["today"]["confirm"]
            heal = city_infos["total"]["heal"]
            dead = city_infos["total"]["dead"]
            details.append([update_time, province, city, confirm, confirm_add, heal, dead])
    return history_data, details

# 连接数据库
def get_conn():
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="root",
        db="yiqing",
        charset="utf8",
        port=3306,
    )
    # 创建游标：
    cursor = conn.cursor()
    return conn, cursor

def close_conn(conn, cursor):
    if cursor:
        cursor.close()
    if conn:
        conn.close()

def update_details(url_last, url_today):
    cursor = None
    conn = None
    try:
        # [['2020-07-01 15:20:46', '北京', '丰台', 266, 0, 43, 0],....]
        detail_data = get_history(url_last, url_today)[1] # 0是字典数据 1是列表数据
        conn, cursor = get_conn()
        sql = "insert into details(update_time,province,city,confirm,confirm_add,heal,dead) values(%s,%s,%s,%s,%s,%s,%s)"
        sql_query = 'select %s=(select update_time from details order by id desc limit 1)' #对比当前最大时间戳,拿到最后一条数据
        cursor.execute(sql_query, detail_data[0][0])
        if not cursor.fetchone()[0]:
            print(f"{time.asctime()}开始更新最新数据")
            for item in detail_data:
                cursor.execute(sql, item)
            conn.commit()  # 提交事务 update delete insert操作
            print(f"{time.asctime()}更新最新数据完毕")
        else:
            print(f"{time.asctime()}已是最新数据！")
    except:
        traceback.print_exc()
    finally:
        close_conn(conn, cursor)

def insert_history(url_last, url_today):
    cursor = None
    conn = None
    try:
        dic = get_history(url_last, url_today)[0]

        print(f"{time.asctime()}开始插入历史数据")
        conn, cursor = get_conn()
        sql = "insert into history values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        for key, value in dic.items():
             # item 格式 {'2020-01-13': {'confirm': 41, 'suspect': 0, 'heal': 0, 'dead': 1}
            cursor.execute(sql, [key, value.get("confirm"), value.get("confirm_add"), value.get("suspect"),
                                 value.get("suspect_add"), value.get("heal"), value.get("heal_add"),
                                 value.get("dead"), value.get("dead_add")])
        conn.commit()  # 提交事务 update delete insert操作
        print(f"{time.asctime()}插入历史数据完毕")
    except:
        traceback.print_exc()
    finally:
        close_conn(conn, cursor)

def update_history(url_last, url_today):
    cursor = None
    conn = None
    try:
        dic = get_history(url_last, url_today)[0]
        print(f"{time.asctime()}开始更新历史数据")
        conn, cursor = get_conn()
        sql = "insert into history values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        sql_query = "select confirm from history where ds=%s"
        for key, value in dic.items():
            # item 格式 {'2020-01-13': {'confirm': 41, 'suspect': 0, 'heal': 0, 'dead': 1}
            if not cursor.execute(sql_query, key):
                cursor.execute(sql, [key, value.get("confirm"), value.get("confirm_add"), value.get("suspect"),
                                     value.get("suspect_add"), value.get("heal"), value.get("heal_add"),
                                     value.get("dead"), value.get("dead_add")])
        conn.commit()
        print(f"{time.asctime()}历史数据更新完毕")
    except:
        traceback.print_exc()
    finally:
        close_conn(conn, cursor)

if __name__ == '__main__':
    # insert_history(url_last, url_today)
    update_details(url_last, url_today)
    update_history(url_last, url_today)





