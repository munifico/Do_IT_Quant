from urllib.request import urlopen
from bs4 import BeautifulSoup
from html_table_parser import parser_functions as parser

import datetime
from file_rw import *

import os
import shutil


# 웹에서 필요한 데이터 크롤링 해오는 함수
def crawl(j_code, c_name):
    url = "http://comp.fnguide.com/SVO2/asp/SVD_Main.asp?pGB=1&gicode=A" + str(j_code) +"&cID=&MenuYn=Y&ReportGB=&NewMenuID=101"
    html = urlopen(url)
    bsObj = BeautifulSoup(html, "html.parser")
    # 웹사이트에서 필요한 부분을 가져오는 코드
    tags = bsObj.find_all("table", attrs={"class":"us_table_ty1 h_fix zigbg_no"})

    # 재무 정보를 제공을 안한 경우 --> [제외]
    if len(tags) < 5:
        return "no_info"
    tags = bsObj.find_all("table", attrs={"class":"us_table_ty1 h_fix zigbg_no"})[4]

    html_table = parser.make2d(tags)
    del html_table[0]

    # 예외처리: 데이터가 적게 제공된 경우
    if len(html_table[0]) < 9:
        for l in html_table:
            if l[0] == 'IFRS(연결)':
                l[0] = "desc"
            if l[0] == 'GAAP(연결)':
                l[0] = "desc"
    else:
        # 필요 없는 데이터 제거
        for l in html_table:
            if l[0] == 'IFRS(연결)':
                l[0] = "desc"
            if l[0] == 'GAAP(연결)':
                l[0] = "desc"
            for _ in range(4):
                del l[1]

    # 만약 추정치인 경우(그 분기의 데이터가 시기상 아직 미정인 경우)
    # 표에 이상하게 표시되므로 보기 좋게 수정
    ## 필수 코드 아님 미관용.
    for i in range(len(html_table[0])):
        if "(E)" in html_table[0][i]:
            html_table[0][i] = html_table[0][i][26:]
        if "(P)" in html_table[0][i]:
            html_table[0][i] = html_table[0][i][24:]

    # null 처리
    for l in html_table[1:]:
        for i in range(len(l)):
            if l[i] == '':
                l[i] = None

    df = pd.DataFrame(data=html_table[1:], index=range(0, len(html_table)-1), columns=html_table[0])
    df.name = c_name

    return df

def dataProcess(df, c_code, tds):

    flag = True
    QuantDataTable = {}
    CompanyDetailTable = {}
    QuantDataTable["cmpName"] = df.name
    QuantDataTable["code"] = c_code
    CompanyDetailTable["code"] = c_code
    CompanyDetailTable["name"] = df.name
    tmp = df[df.columns[0]]

    if tds not in df.columns:
        return "no_info", "no_info"

    for i in range(len(df[tds])):
        # 2020/03 데이터가 있는지 확인
        if df[tds][i] != None:
            flag = False

        # 2020/03 데이터가 없으면 return
        if flag:
            return "no_info", "no_info"

        # 데이터 타입 처리
        if type(df[tds][i]) != type(None):
            if df[tds][i] == "완전잠식":
                df[tds][i] = None
            elif df[tds][i] == "N/A":
                df[tds][i] = None
            elif df[tds][i] != "완전잠식":
                if df[tds][i] != "N/A":
                    if ',' in df[tds][i]:
                        df[tds][i] = df[tds][i].replace(',', '')
                    df[tds][i] = float(df[tds][i])

        # QuantDataTable
        if 'PER' in tmp[i]:
            QuantDataTable['per'] = df[tds][i]
        elif 'PBR' in tmp[i]:
            QuantDataTable['pbr'] = df[tds][i]
        elif 'ROA' in tmp[i]:
            QuantDataTable['roa'] = df[tds][i]
        elif 'ROE' in tmp[i]:
            QuantDataTable['roe'] = df[tds][i]
        elif '부채비율' in tmp[i]:
            QuantDataTable['debtRatio'] = df[tds][i]
        elif '영업이익률' in tmp[i]:
            QuantDataTable['operatingProfitRatio'] = df[tds][i]
        elif '유보율' in tmp[i]:
            QuantDataTable['reserveRatio'] = df[tds][i]

        # CompanyDetailTable
        # 종가는 매일 갱신
        elif tmp[i] == '자산총계':
            CompanyDetailTable['totalAsset'] = df[tds][i]
        elif tmp[i] == '자본총계':
            CompanyDetailTable['totalEquity'] = df[tds][i]
        elif tmp[i] == '부채총계':
            CompanyDetailTable['totalDebt'] = df[tds][i]
        elif tmp[i] == '매출액':
            CompanyDetailTable['sales'] = df[tds][i]
        elif tmp[i] == '영업이익':
            CompanyDetailTable['operatingProfit'] = df[tds][i]
        elif tmp[i] == '당기손이익':
            CompanyDetailTable['netIncome'] = df[tds][i]

    return QuantDataTable, CompanyDetailTable

def crawl2(c_code):
    url = "http://comp.fnguide.com/SVO2/asp/SVD_Finance.asp?pGB=1&gicode=A" + str(c_code) + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=103&stkGb=701"
    html = urlopen(url)
    bsObj = BeautifulSoup(html, "html.parser")

    tables = bsObj.find_all("table", attrs={"class":"us_table_ty1 h_fix zigbg_no"})

    if len(tables) < 3:
        return "no_info"

    table = tables[2]
    html_table = parser.make2d(table)
    flag = True
    cnt = 0
    for row in html_table:
        if "이익잉여금" in row[0]:
            flag = False
            ri = cnt - 1
        # null 처리
        for i in range(len(row)):
            if row[i] == '':
                row[i] = None
        cnt += 1
    # 이익잉여금 정보 없으면 return
    if flag:
        return "no_info"

    df = pd.DataFrame(data=html_table[1:], index=range(0, len(html_table)-1), columns=html_table[0])
    d = df.columns[len(df.columns)-1]

    return str(df[d].iloc[ri])


def setTime():
    now = datetime.datetime.now()
    nowDate = now.strftime('%Y_%m_%d')
    nds = str(nowDate)
    nds += '_'
    nds_l = nds.split('_')
    y = int(nds_l[0])
    m = int(nds_l[1])
    if 3 < m <= 12:
        tds = str(y) + '/03'
    else:
        tds = str(y - 1) + '/12'

    return str(nds), str(tds)



jongmok_code = ExcelRead("./data/sangjang_jongmokCode.xlsx")
QTable = []
CTable = []
no_info = []

nds, tds = setTime()

for i in jongmok_code.index:
  c_name = jongmok_code.iloc[i]["회사명"]
  c_code = str(jongmok_code.iloc[i]["종목코드"])
  market = jongmok_code.iloc[i]["업종"]
  desc = jongmok_code.iloc[i]["주요제품"]
  if len(c_code) < 6:
      ii = 6 - len(c_code)
      c_code = '0' * ii + str(c_code)
  df = crawl(c_code, c_name)
  if type(df) == type("no_info"):
      no_info.append(c_name)
  else:
      Qdata, Cdata = dataProcess(df, c_code, tds)
      if type(Qdata) == type("no_info"):
          no_info.append(c_name)
      else:
          Cdata["description"] = desc
          Cdata["market"] = market
          retainedEarnings = crawl2(c_code)
          if retainedEarnings == "no_info":
              no_info.append(c_name)
          else:
              Cdata["retainedEarnings"] = retainedEarnings
              QTable.append(Qdata)
              CTable.append(Cdata)


no_info = set(no_info)
no_info = list(no_info)

fn1 = './data/' + str(nds) + '/QuantDataTable.json'
fn2 = './data/' + str(nds) + '/CompanyDetailTable.json'
fn3 = './data/' + str(nds) + '/no_info.json'

dn = './data/' + str(nds)
if os.path.isdir(dn):
    shutil.rmtree(dn)
os.mkdir(dn)

#json 파일로 저장
JsonWrite(fn1, QTable)
JsonWrite(fn2, CTable)
JsonWrite(fn3, no_info)
