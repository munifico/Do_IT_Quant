from urllib.request import urlopen
from bs4 import BeautifulSoup
from html_table_parser import parser_functions as parser

import datetime
# 파일 입출력 담당
from file_rw import *

import os
# delete directory and files at once
import shutil


def crawl(c_code):

    url = "http://www.thinkpool.com/itemanal/i/chart.jsp?code="
    url += str(c_code)
    html = urlopen(url)
    soup = BeautifulSoup(html, 'html.parser')

    table = soup.find("table", attrs={"class":"tbl1"})

    if type(table) == type(None):
        return -1

    trs = table.find_all('tr')

    for tr in trs:
        if "전일종가" in str(tr):
            tds = tr.find_all('td')
            jongga = tds[0].text.strip()

    return jongga


jongmok_code = ExcelRead("./data/sangjang_jongmokCode.xlsx")
jongga_data = {}
no_jongga = []

for i in jongmok_code.index:
    c_name = jongmok_code.iloc[i]["회사명"]
    jongga_data[c_name] = {}
    c_code = str(jongmok_code.iloc[i]["종목코드"])
    if len(c_code) < 6:
        ii = 6 - len(c_code)
        c_code = '0' * ii + str(c_code)
    jongga = crawl(c_code)
    if jongga == -1:
        no_jongga.append(c_name)
        del jongga_data[c_name]
    else:
        jongga = jongga.replace(',', '')
        jongga_data[c_name]["code"] = c_code
        jongga_data[c_name]["endPrice"] = jongga


now = datetime.datetime.now()
nowDate = now.strftime('%Y_%m_%d')
nds = str(nowDate)

fn1 = './data/' + str(nds) + '/jongga.json'
fn2 = './data/' + str(nds) + '/no_jongga.json'

dn = './data/' + str(nds)
if os.path.isdir(dn):
    shutil.rmtree(dn)
os.mkdir(dn)

#json 파일로 저장
JsonWrite(fn1, jongga_data)
JsonWrite(fn2, no_jongga)
