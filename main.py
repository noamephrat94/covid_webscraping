from selenium import webdriver
import time
from bs4 import BeautifulSoup
from PIL import Image
import pandas as pd
import requests
import pytesseract
from PIL import Image
from tika import parser  # pip install tika
import re
import requests
import pdfplumber
import io
from datetime import datetime
import wget
import os
import glob
import streamlit as st

today = datetime.today().strftime('%d-%m-%Y')
day = datetime.today().strftime('%d')
month = datetime.today().strftime('%m')
year = datetime.today().strftime('%Y')

def prep_driver():
    driver_location = 'driver/chromedriver'
    options = webdriver.ChromeOptions()
    options.add_argument('--lang=es')
    options.add_argument("--headless")
    driver = webdriver.Chrome(executable_path=driver_location, chrome_options=options)
    return driver

def load_page_comps(driver):
    url = f'https://coronavirus.al/'
    driver.get(url)
    driver.maximize_window()

def access_elements(nums, list_index):
    result = [nums[i] for i in list_index]
    return result

def albania(driver, df):
    country = 'ALBANIA'
    st.write("Scraping Albania...")
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = []

    cases = soup.find('div', class_='prekur')
    total_cases = cases.find("strong")
    new_cases = cases.find("span")

    deaths = soup.find('div', class_='vdekur')
    total_deaths = deaths.find("strong")
    new_deaths = deaths.find("span")

    driver.get("https://coronavirus.al/statistika/")
    time.sleep(2)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    page2 = soup.find('div', class_='card stats_teste_gjithsej')
    new = page2.findAll("span")

    table = soup.findAll('tr')
    td = table[len(table)-1]
    data = td.findAll('td', class_='tg-w6oh')
    data = data[1:3]

    print(f"Total cases: {str(total_cases).replace('<strong>', '').replace('</strong>', '')}")
    print(f"New cases: {str(new_cases).replace('<span>(', '').replace(')</span>', '').replace('+', '')}")
    print(f"Total deaths:{str(total_deaths).replace('<strong>', '').replace('</strong>', '')}")
    print(f"New deaths: {str(new_deaths).replace('<span>(', '').replace(')</span>', '').replace('+', '')}")
    print(f"tests last 24h: {str(new[0]).replace('<span>(', '').replace(')</span>', '').replace('+', '')}")
    print(f"icu: {str(data[0]).split('>')[1].split('<')[0]}")
    print(f"hospitalizations: {str(data[1]).split('>')[1].split('<')[0]}")

    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = str(total_cases).replace('<strong>', '').replace('</strong>', '')
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = str(total_deaths).replace('<strong>', '').replace('</strong>', '')
    df.loc[df['ADM0NAME'] == country, ['CasesNew']] = str(new_cases).replace('<span>(', '').replace(')</span>', '').replace('+', '')
    df.loc[df['ADM0NAME'] == country, ['DeathsNew']] = str(new_deaths).replace('<span>(', '').replace(')</span>', '').replace('+', '')
    df.loc[df['ADM0NAME'] == country, ['test']] = str(new[0]).replace('<span>(', '').replace(')</span>', '').replace('+', '')
    df.loc[df['ADM0NAME'] == country, ['hospital']] = str(data[1]).split('>')[1].split('<')[0]
    df.loc[df['ADM0NAME'] == country, ['ICU']] = str(data[0]).split('>')[1].split('<')[0]

    return df

def andorra(driver, df):
    country='ANDORRA'
    st.write("Scraping andorra...")
    url = f'https://www.govern.ad/covid/taula.php'
    driver.get(url)
    time.sleep(3)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = soup.findAll('div', class_='row text-center')
    data = data[0]
    col2 = data.find('div', class_='col-2')
    col3 = data.findAll('div', class_='col-3')
    cases = str(col2).replace('<div class="col-2" style="border-bottom:1px solid #B1CDDB; border-right:1px solid #B1CDDB; border-top:1px solid #B1CDDB;">','').replace('</div>','').replace("\t", '').replace("\n", '')
    print(f"Total cases: {cases.split('<br/>')[1]}")
    d = []
    [d.append(str(i).replace('<div class="col-3" style="border-bottom:1px solid #B1CDDB; border-right:1px solid #B1CDDB; border-top:1px solid #B1CDDB;">', '').replace('</div>','').replace("\t", '').replace("\n", '')) for i in col3]
    print(f"Hospitalizations: {d[0].split('<br/>')[1]}")
    print(f"Total deaths: {d[1].split('<br/>')[1]}")
    print("Done Scraping andorra\n")

    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = cases.split('<br/>')[1]
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = d[1].split('<br/>')[1]
    df.loc[df['ADM0NAME'] == country, ['hospital']] = d[0].split('<br/>')[1]
    return df

def bulgaria(driver, df):
    country='BULGARIA'
    st.write("Scraping Bulgaria...")
    url = f'https://coronavirus.bg/bg/1'
    driver.get(url)
    time.sleep(3)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    new_cases = soup.find('h4', class_='news-title')
    new_cases = str(new_cases).split('>')[1].split(" ")[0]
    print("new cases", new_cases)
    data = soup.findAll('div', class_='col-lg-3 col-md-6')
    word_filters = ['Потвърдени случая', 'Хоспитализирани', 'Починали']
    filtered = []
    numbers = []
    for d in data:
        for word in word_filters:
            if word in str(d):
                value = (str(d.findAll('p')[0]).split('>')[1].split('<')[0].replace(' ', ''))
                if 'Потвърдени случая' not in str(d):
                    sub_value =str(d.find('p', class_='statistics-subvalue')).replace('<p class="statistics-subvalue">','').replace('</p>','')
                    numbers.append(re.sub("[^0-9a-zA-Z]+", "", value))
                    numbers.append(re.sub("[^0-9a-zA-Z]+", "", sub_value))
                else:
                    numbers.append(re.sub("[^0-9a-zA-Z]+", "", value))

            filtered.append(d)
    print(f"Total cases: {numbers[0]}")
    print(f"Hospitalizations: {numbers[1]}")
    print(f"icu: {numbers[2]}")
    print(f"Total deaths: {numbers[3]}")
    print(f"New deaths: {numbers[4]}")

    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = numbers[0]
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = numbers[3]
    df.loc[df['ADM0NAME'] == country, ['CasesNew']] = new_cases
    df.loc[df['ADM0NAME'] == country, ['DeathsNew']] = numbers[4]
    df.loc[df['ADM0NAME'] == country, ['hospital']] = numbers[1]
    df.loc[df['ADM0NAME'] == country, ['ICU']] = numbers[2]

    print("Done Scraping Bulgaria\n")
    return df

    # print(filtered)

def monaco(driver, df):
    country = 'MONACO'
    st.write("Scraping Monaco...")
    url = f'https://covid19.mc/en/key-figures/'
    driver.get(url)
    time.sleep(3)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = soup.findAll('div', class_='accordion')
    spans = []
    for d in data:
        spans.append(d.findAll("span"))
    list_index = [0, 1, 5]
    data = access_elements(spans, list_index)
    print(f"New cases: {str(data[0][0]).split('>')[1].split('<')[0]}, Total cases: {str(data[0][1]).split('>')[1].split('<')[0]}")
    print(f"Hospitalizations: {str(data[1]).split('>')[1].split('<')[0]}")
    print(f"New deaths: {str(data[2][0]).split('>')[1].split('<')[0]}, Total deaths: {str(data[2][1]).split('>')[1].split('<')[0]}")

    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = str(data[0][1]).split('>')[1].split('<')[0]
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = str(data[2][1]).split('>')[1].split('<')[0]
    df.loc[df['ADM0NAME'] == country, ['CasesNew']] = str(data[0][0]).split('>')[1].split('<')[0]
    df.loc[df['ADM0NAME'] == country, ['DeathsNew']] = str(data[2][0]).split('>')[1].split('<')[0]
    df.loc[df['ADM0NAME'] == country, ['hospital']] = str(data[1]).split('>')[1].split('<')[0]
    print("Done Scraping Monaco\n")
    return df

def serbia(driver, df):
    country = 'SERBIA'
    st.write("Scraping Serbia...")
    url = f'https://covid19.rs/homepage-english/'
    driver.get(url)
    time.sleep(3)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = soup.findAll('p', class_='elementor-heading-title elementor-size-default')
    list_index = [2, 4, 10, 12, 14, 16, 18]
    data = access_elements(data, list_index)
    print(f"Total cases: {str(data[0]).split('>')[1].split('<')[0]}")
    print(f"Total deaths: {str(data[1]).split('>')[1].split('<')[0]}")
    print(f"tested in last 24 hours: {str(data[2]).split('>')[1].split('<')[0]}")
    print(f"cases last 24 hours: {str(data[3]).split('>')[1].split('<')[0]}")
    print(f"deaths last 24 hours: {str(data[4]).split('>')[1].split('<')[0]}")
    print(f"hospitalizations: {str(data[5]).split('>')[1].split('<')[0]}")
    print(f"critical: {str(data[6]).split('>')[1].split('<')[0]}")

    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = str(data[0]).split('>')[1].split('<')[0].replace(",","")
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = str(data[1]).split('>')[1].split('<')[0].replace(",","")
    df.loc[df['ADM0NAME'] == country, ['CasesNew']] = str(data[3]).split('>')[1].split('<')[0].replace(",","")
    df.loc[df['ADM0NAME'] == country, ['DeathsNew']] = str(data[4]).split('>')[1].split('<')[0].replace(",","")
    df.loc[df['ADM0NAME'] == country, ['test']] = str(data[2]).split('>')[1].split('<')[0].replace(",","")
    df.loc[df['ADM0NAME'] == country, ['hospital']] = str(data[5]).split('>')[1].split('<')[0].replace(",","")
    df.loc[df['ADM0NAME'] == country, ['ICU']] = str(data[6]).split('>')[1].split('<')[0].replace(",","")
    print("Done Scraping Serbia\n")
    return df

def denmark(driver, df):
    country = 'DENMARK'
    st.write("Scraping denmark...")
    new_cases = 'https://services5.arcgis.com/Hx7l9qUpAnKPyvNz/arcgis/rest/services/DB_kommunalt_data_gdb/FeatureServer/23/query?f=json&cacheHint=true&orderByFields=&outFields=*&outStatistics=%5B%7B%22onStatisticField%22%3A%22totalinfections_diff%22%2C%22outStatisticFieldName%22%3A%22value%22%2C%22statisticType%22%3A%22sum%22%7D%5D&resultType=standard&returnGeometry=false&spatialRel=esriSpatialRelIntersects&where=1%3D1'
    new_deaths = 'https://services5.arcgis.com/Hx7l9qUpAnKPyvNz/arcgis/rest/services/DB_kommunalt_data_gdb/FeatureServer/23/query?f=json&cacheHint=true&orderByFields=&outFields=*&outStatistics=%5B%7B%22onStatisticField%22%3A%22deaths_diff%22%2C%22outStatisticFieldName%22%3A%22value%22%2C%22statisticType%22%3A%22sum%22%7D%5D&resultType=standard&returnGeometry=false&spatialRel=esriSpatialRelIntersects&where=1%3D1'
    total_cases = 'https://services5.arcgis.com/Hx7l9qUpAnKPyvNz/arcgis/rest/services/DB_kommunalt_data_gdb/FeatureServer/23/query?f=json&cacheHint=true&orderByFields=&outFields=*&outStatistics=%5B%7B%22onStatisticField%22%3A%22totalinfections_today%22%2C%22outStatisticFieldName%22%3A%22value%22%2C%22statisticType%22%3A%22sum%22%7D%5D&resultType=standard&returnGeometry=false&spatialRel=esriSpatialRelIntersects&where=1%3D1'
    total_deaths = 'https://services5.arcgis.com/Hx7l9qUpAnKPyvNz/arcgis/rest/services/DB_kommunalt_data_gdb/FeatureServer/23/query?f=json&cacheHint=true&orderByFields=&outFields=*&outStatistics=%5B%7B%22onStatisticField%22%3A%22deaths_today%22%2C%22outStatisticFieldName%22%3A%22value%22%2C%22statisticType%22%3A%22sum%22%7D%5D&resultType=standard&returnGeometry=false&spatialRel=esriSpatialRelIntersects&where=1%3D1'
    new_icu = 'https://services5.arcgis.com/Hx7l9qUpAnKPyvNz/arcgis/rest/services/DB_kommunalt_data_gdb/FeatureServer/23/query?f=json&cacheHint=true&orderByFields=&outFields=*&outStatistics=%5B%7B%22onStatisticField%22%3A%22admissions_intensive_today%22%2C%22outStatisticFieldName%22%3A%22value%22%2C%22statisticType%22%3A%22sum%22%7D%5D&resultType=standard&returnGeometry=false&spatialRel=esriSpatialRelIntersects&where=1%3D1'
    total_icu = 'https://services5.arcgis.com/Hx7l9qUpAnKPyvNz/arcgis/rest/services/DB_kommunalt_data_gdb/FeatureServer/23/query?f=json&cacheHint=true&orderByFields=&outFields=*&outStatistics=%5B%7B%22onStatisticField%22%3A%22admissions_today%22%2C%22outStatisticFieldName%22%3A%22value%22%2C%22statisticType%22%3A%22sum%22%7D%5D&resultType=standard&returnGeometry=false&spatialRel=esriSpatialRelIntersects&where=1%3D1'
    new_cases = requests.get(url=new_cases).json()
    new_deaths = requests.get(url=new_deaths).json()
    total_cases = requests.get(url=total_cases).json()
    total_deaths = requests.get(url=total_deaths).json()
    new_icu = requests.get(url=new_icu).json()
    total_icu = requests.get(url=total_icu).json()
    print(f"New cases: {new_cases['features'][0]['attributes']['value']}")
    print(f"New Deaths: {new_deaths['features'][0]['attributes']['value']}")
    print(f"Total cases: {total_cases['features'][0]['attributes']['value']}")
    print(f"Total deaths: {total_deaths['features'][0]['attributes']['value']}")
    print(f"icu: {new_icu['features'][0]['attributes']['value']}")
    print(f"Hospitalization: {total_icu['features'][0]['attributes']['value']}")

    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = total_cases['features'][0]['attributes']['value']
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = total_deaths['features'][0]['attributes']['value']
    df.loc[df['ADM0NAME'] == country, ['CasesNew']] = new_cases['features'][0]['attributes']['value']
    df.loc[df['ADM0NAME'] == country, ['DeathsNew']] = new_deaths['features'][0]['attributes']['value']
    df.loc[df['ADM0NAME'] == country, ['hospital']] = total_icu['features'][0]['attributes']['value']
    df.loc[df['ADM0NAME'] == country, ['ICU']] = new_icu['features'][0]['attributes']['value']

    print("Done Scraping denmark\n")
    return df

def sanmarino(driver, df):
    country = 'SAN MARINO'
    st.write("Scraping san-marino...")
    url = f'https://www.pa.sm/SASVisualAnalyticsViewer/VisualAnalyticsViewer_guest.jsp?reportSBIP=SBIP%3A%2F%2FMETASERVER%2FShared%20Data%2FReportGuest%2FCOVID19%20-%20Cruscotto%20Pubblico(Report)&page=vi1&informationEnabled=false&commentsEnabled=false&reportViewOnly=true&reportContextBar=false'
    driver.get(url)
    time.sleep(30)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = soup.findAll('div', class_='vavRichTextWrapper')
    list_index = [4, 8, 9]
    data = access_elements(data, list_index)
    print(f"Total cases: {str(data[2].findAll('span')[1]).split('>')[1].split('<')[0]}")
    print(f"Total deaths: {str(data[1].findAll('span')[1]).split('>')[1].split('<')[0]}")
    print(f"Hospitalizations: {str(data[0].findAll('span')[1]).split('>')[1].split('<')[0]}")

    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = str(data[2].findAll('span')[1]).split('>')[1].split('<')[0]
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = str(data[1].findAll('span')[1]).split('>')[1].split('<')[0]
    df.loc[df['ADM0NAME'] == country, ['hospital']] = str(data[0].findAll('span')[1]).split('>')[1].split('<')[0]

    print("Done Scraping san-marino\n")
    return df

def slovakia(driver, df):
    country = 'SLOVAKIA'
    st.write("Scraping slovakia...")
    url = f'https://covid-19.nczisk.sk/sk'
    driver.get(url)
    time.sleep(10)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = soup.findAll('div', class_='to-target chart-value')
    list_index = [1, 2, 3]
    data = access_elements(data, list_index)
    print(f"Total cases: {''.join(str(data[0].findAll('span')[0]).split('<!-- -->')[1].split('<!-- -->')[0].split())}")
    print(f"New cases: {''.join(str(data[0].findAll('small')[0]).split('<!-- -->')[1].split('<!-- -->')[0].split())}")
    print(f"Total deaths: {''.join(str(data[1].findAll('span')[0]).split('<!-- -->')[1].split('<!-- -->')[0].split())}")
    print(f"New deaths: {''.join(str(data[1].findAll('small')[0]).split('<!-- -->')[1].split('<!-- -->')[0].split())}")
    print(f"Hospitalizations: {''.join(str(data[2].findAll('span')[0]).split('<!-- -->')[1].split('<!-- -->')[0].split())}")

    url = f'https://korona.gov.sk/'
    driver.get(url)
    time.sleep(5)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data2 = soup.findAll('p', class_='govuk-body')
    data2 = data2[2].find('strong')
    print(f"icu: {str(data2).replace('<strong>', '').replace('</strong>', '')}")

    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = ''.join(str(data[0].findAll('span')[0]).split('<!-- -->')[1].split('<!-- -->')[0].split())
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = ''.join(str(data[1].findAll('span')[0]).split('<!-- -->')[1].split('<!-- -->')[0].split())
    df.loc[df['ADM0NAME'] == country, ['CasesNew']] = ''.join(str(data[0].findAll('small')[0]).split('<!-- -->')[1].split('<!-- -->')[0].split())
    df.loc[df['ADM0NAME'] == country, ['DeathsNew']] = ''.join(str(data[1].findAll('small')[0]).split('<!-- -->')[1].split('<!-- -->')[0].split())
    df.loc[df['ADM0NAME'] == country, ['hospital']] = ''.join(str(data[2].findAll('span')[0]).split('<!-- -->')[1].split('<!-- -->')[0].split())
    df.loc[df['ADM0NAME'] == country, ['ICU']] = str(data2).replace('<strong>', '').replace('</strong>', '')


    print("Done Scraping slovakia\n")
    return df

def turkey(driver, df):
    country = 'TURKEY'
    st.write("Scraping turkey...")
    url = f'https://covid19.saglik.gov.tr/TR-66935/genel-koronavirus-tablosu.html'
    driver.get(url)
    time.sleep(3)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = soup.findAll('tbody', id='haftalikveriler')
    data = data[0].findAll('td')
    Number_of_Cases_per_Week = data[1]
    Weekly_Number_of_Deaths = data[2]
    Total_Number_of_Cases = data[4]
    Total_Number_of_Deaths = data[5]
    print(f"Weekly Number of cases: {str(Number_of_Cases_per_Week).replace('.','').replace('<td>','').replace('</td>','')}")
    print(f"Weekly Number of Deaths: {str(Weekly_Number_of_Deaths).replace('.','').replace('<td>','').replace('</td>','')}")
    print(f"Total Number of Cases: {str(Total_Number_of_Cases).replace('.','').replace('<td>','').replace('</td>','')}")
    print(f"Total Number of Deaths: {str(Total_Number_of_Deaths).replace('.','').replace('<td>','').replace('</td>','')}")

    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = str(Total_Number_of_Cases).replace('.','').replace('<td>','').replace('</td>','')
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = str(Total_Number_of_Deaths).replace('.','').replace('<td>','').replace('</td>','')
    df.loc[df['ADM0NAME'] == country, ['CasesNew']] = str(Number_of_Cases_per_Week).replace('.','').replace('<td>','').replace('</td>','')
    df.loc[df['ADM0NAME'] == country, ['DeathsNew']] = str(Weekly_Number_of_Deaths).replace('.','').replace('<td>','').replace('</td>','')

    print("Done Scraping turkey\n")
    return df

def belgium(driver, df):
    country = 'BELGIUM'
    st.write("Scraping belgium...")
    url = f'https://datastudio.google.com/embed/u/0/reporting/c14a5cfc-cab7-4812-848c-0369173148ab/page/tpRKB'
    driver.get(url)
    time.sleep(12)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = soup.findAll('div', class_='valueLabel')
    cases = str(data[0]).split('>')[1].split('<')[0].replace('\n', '').replace(" ", "").replace(",", "")
    print(f"Total cases: {cases}")
    url = 'https://datastudio.google.com/embed/reporting/c14a5cfc-cab7-4812-848c-0369173148ab/page/QTSKB'
    driver.get(url)
    time.sleep(10)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = soup.findAll('div', class_='valueLabel')
    deaths = str(data[0]).split('>')[1].split('<')[0].replace('\n', '').replace(" ", "").replace(",", "")
    print(f"Total deaths: {deaths}")

    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = cases
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = deaths


    print("Done Scraping belgium")
    return df

def norway(driver, df):
    country = 'NORWAY'
    st.write("Scraping norway...")
    url = f'https://www.fhi.no/en/id/infectious-diseases/coronavirus/daily-reports/daily-reports-COVID19/'
    driver.get(url)
    time.sleep(12)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = soup.findAll('div', class_='c-key-figure__number')

    deaths = str(data[2]).split(';">')[1].split('<')[0].replace('\n', '').replace(",", "")
    cases = str(data[3]).split(';">')[1].split('<')[0].replace('\n', '').replace(",", "")
    print(cases)
    print(deaths)

    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = cases
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = deaths


    print("Done Scraping norway")
    return df

def malta(driver, df):
    country = 'MALTA'
    st.write("Scraping malta...")
    url = f'https://github.com/COVID19-Malta/COVID19-Data/blob/master/COVID-19%20Malta%20-%20Aggregate%20Data%20Set.csv'
    driver.get(url)
    time.sleep(3)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = soup.findAll('tr', class_='js-file-line')
    data = data[len(data)-1]
    data = data.findAll('td')
    new_cases = data[2]
    total_cases = data[3]
    total_deaths = data[5]
    print(
        f"New cases: {str(new_cases).replace('.', '').replace('<td>', '').replace('</td>', '')}")
    print(
        f"Total cases: {str(total_cases).replace('.', '').replace('<td>', '').replace('</td>', '')}")
    print(
        f"Total Deaths: {str(total_deaths).replace('.', '').replace('<td>', '').replace('</td>', '')}")


    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = str(total_cases).replace('.', '').replace('<td>', '').replace('</td>', '')
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = str(total_deaths).replace('.', '').replace('<td>', '').replace('</td>', '')
    df.loc[df['ADM0NAME'] == country, ['CasesNew']] = str(new_cases).replace('.', '').replace('<td>', '').replace('</td>', '')

    print("Done Scraping malta\n")
    return df

def kaz(driver):
    img = '/Users/admin/Downloads/kaz.png'

    print(pytesseract.get_languages(config=''))
    print(pytesseract.image_to_string(Image.open(img)))

def france(driver):
    st.write("Scraping france...")
    url = f'https://dashboard.santepubliquefrance.fr/digdash_dashboard_spf/index.html?domain=ddenterpriseapi_spf&user=spf&pass=spf#2'
    driver.get(url)
    time.sleep(20)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = soup.findAll('div', id='SPF_Chiffres_clés_groupsofcolumns_Suivi_epidemie_groupsofcolumns_fee2a6ab')
    # daily_cases = data[0]
    print(data)
    # Number_of_Cases_per_Week = data[1]
    # Weekly_Number_of_Deaths = data[2]
    # Total_Number_of_Cases = data[4]
    # Total_Number_of_Deaths = data[5]
    # print(
    #     f"Weekly Number of cases: {str(Number_of_Cases_per_Week).replace('.', '').replace('<td>', '').replace('</td>', '')}")
    # print(
    #     f"Weekly Number of Deaths: {str(Weekly_Number_of_Deaths).replace('.', '').replace('<td>', '').replace('</td>', '')}")
    # print(
    #     f"Total Number of Cases: {str(Total_Number_of_Cases).replace('.', '').replace('<td>', '').replace('</td>', '')}")
    # print(
    #     f"Total Number of Deaths: {str(Total_Number_of_Deaths).replace('.', '').replace('<td>', '').replace('</td>', '')}")
    #
    # print("Done Scraping france\n")

def poland(driver, df):
    country = 'POLAND'
    st.write("Scraping poland...")
    new_cases = 'https://services-eu1.arcgis.com/zk7YlClTgerl62BY/arcgis/rest/services/global_corona_actual_widok3/FeatureServer/0/query?f=json&cacheHint=true&orderByFields=&outFields=*&outStatistics=%5B%7B%22onStatisticField%22%3A%22dzienne_wszystkie_zakazenia%22%2C%22outStatisticFieldName%22%3A%22value%22%2C%22statisticType%22%3A%22sum%22%7D%5D&resultType=standard&returnGeometry=false&spatialRel=esriSpatialRelIntersects'
    new_deaths = 'https://services-eu1.arcgis.com/zk7YlClTgerl62BY/arcgis/rest/services/global_corona_actual_widok3/FeatureServer/0/query?f=json&cacheHint=true&orderByFields=&outFields=*&outStatistics=%5B%7B%22onStatisticField%22%3A%22ZGONY_DZIENNE%22%2C%22outStatisticFieldName%22%3A%22value%22%2C%22statisticType%22%3A%22sum%22%7D%5D&resultType=standard&returnGeometry=false&spatialRel=esriSpatialRelIntersects'
    total_cases = 'https://services-eu1.arcgis.com/zk7YlClTgerl62BY/arcgis/rest/services/global_corona_actual_widok3/FeatureServer/0/query?f=json&cacheHint=true&orderByFields=&outFields=*&outStatistics=%5B%7B%22onStatisticField%22%3A%22liczba_wszystkich_zakazen%22%2C%22outStatisticFieldName%22%3A%22value%22%2C%22statisticType%22%3A%22sum%22%7D%5D&resultType=standard&returnGeometry=false&spatialRel=esriSpatialRelIntersects'
    total_deaths = 'https://services-eu1.arcgis.com/zk7YlClTgerl62BY/arcgis/rest/services/global_corona_actual_widok3/FeatureServer/0/query?f=json&cacheHint=true&orderByFields=&outFields=*&outStatistics=%5B%7B%22onStatisticField%22%3A%22LICZBA_ZGONOW%22%2C%22outStatisticFieldName%22%3A%22value%22%2C%22statisticType%22%3A%22sum%22%7D%5D&resultType=standard&returnGeometry=false&spatialRel=esriSpatialRelIntersects'

    new_cases = requests.get(url=new_cases).json()
    new_deaths = requests.get(url=new_deaths).json()
    total_cases = requests.get(url=total_cases).json()
    total_deaths = requests.get(url=total_deaths).json()

    print(f"New cases: {new_cases['features'][0]['attributes']['value']}")
    print(f"New Deaths: {new_deaths['features'][0]['attributes']['value']}")
    print(f"Total cases: {total_cases['features'][0]['attributes']['value']}")
    print(f"Total deaths: {total_deaths['features'][0]['attributes']['value']}")

    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = total_cases['features'][0]['attributes']['value']
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = total_deaths['features'][0]['attributes']['value']
    df.loc[df['ADM0NAME'] == country, ['CasesNew']] = new_cases['features'][0]['attributes']['value']
    df.loc[df['ADM0NAME'] == country, ['DeathsNew']] = new_deaths['features'][0]['attributes']['value']

    print("Done Scraping poland\n")
    return df

def germany(driver, df):
    country = 'GERMANY'
    st.write("Scraping germany...")
    all_stats = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/rki_key_data_v/FeatureServer/0/query?f=json&where=AnzTodesfall%3C%3E0&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=*&orderByFields=AdmUnitId%20asc&resultOffset=0&resultRecordCount=1&resultType=standard&cacheHint=true'
    all_stats = requests.get(url=all_stats).json()
    total_cases = all_stats['features'][0]['attributes']['AnzFall']
    total_deaths = all_stats['features'][0]['attributes']['AnzTodesfall']
    new_cases = all_stats['features'][0]['attributes']['AnzFallNeu']
    new_deaths = all_stats['features'][0]['attributes']['AnzTodesfallNeu']

    print(f"New cases: {new_cases}")
    print(f"New Deaths: {new_deaths}")
    print(f"Total cases: {total_cases}")
    print(f"Total deaths: {total_deaths}")

    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = total_cases
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = total_deaths
    df.loc[df['ADM0NAME'] == country, ['CasesNew']] = new_cases
    df.loc[df['ADM0NAME'] == country, ['DeathsNew']] = new_deaths

    print("Done Scraping germany\n")
    return df

def kosovo(driver, df):
    country = 'KOSOVO'
    st.write("Scraping kosovo...")
    url = f'https://datastudio.google.com/embed/reporting/2e546d77-8f7b-4c35-8502-38533aa0e9e8/page/tI3oB'
    driver.get(url)
    time.sleep(45)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = soup.findAll('div', class_='valueLabel')
    hospital = str(data[8]).split('>')[1].split('<')[0].replace('\n', '').replace(" ", "")
    icu = str(data[10]).split('>')[1].split('<')[0].replace('\n', '').replace(" ", "")

    print(f"Total hospital: {hospital}")
    print(f"Total icu: {icu}")

    df.loc[df['ADM0NAME'] == country, ['hospital']] = hospital
    df.loc[df['ADM0NAME'] == country, ['ICU']] = icu

    print("Done Scraping kosovo")
    return df

def jersey(driver, df):
    country = 'JERSEY'
    st.write("Scraping jersey...")
    url = f'https://www.gov.je/Health/Coronavirus/Pages/CoronavirusCases.aspx#tab_totalsSinceMarch'
    driver.get(url)
    time.sleep(5)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = soup.findAll('h3', class_='text-white my-0')
    total_cases = str(data[3]).replace(",", "").split(">")[1].split("<")[0]
    total_deaths = str(data[5]).replace(",", "").split(">")[1].split("<")[0]
    print(total_cases)
    print(total_deaths)
    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = total_cases
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = total_deaths

    print("Done Scraping jersey\n")
    return df

def ireland(driver, df):
    country = 'IRELAND'
    st.write("Scraping ireland...")
    url = f'https://geohive.maps.arcgis.com/apps/dashboards/3cd9871b9c534ee9a2cad7a5eaf9be7c'
    driver.get(url)
    time.sleep(12)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = soup.findAll('g', class_='responsive-text-label')
    total_cases = str(data[1]).replace(",", "").replace("\n", "").replace(" ", "").split('stroke">')[1].split("<")[0]
    total_deaths = str(data[10]).replace(",", "").replace("\n", "").replace(" ", "").split('stroke">')[1].split("<")[0]
    icu = str(data[16]).replace(",", "").replace("\n", "").replace(" ", "").split('stroke">')[1].split("<")[0]
    hospital = str(data[19]).replace(",", "").replace("\n", "").replace(" ", "").split('stroke">')[1].split("<")[0]

    print(f'total_cases: {total_cases}')
    print(f'total_deaths: {total_deaths}')
    print(f'hospital: {hospital}')
    print(f'icu: {icu}')

    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = total_cases
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = total_deaths
    df.loc[df['ADM0NAME'] == country, ['hospital']] = hospital
    df.loc[df['ADM0NAME'] == country, ['ICU']] = icu
    print("Done Scraping ireland\n")
    return df

def guernsey(driver, df):
    country = 'GUERNSEY'
    st.write("Scraping guernsey...")
    url = f'https://covid19.gov.gg/'
    driver.get(url)
    time.sleep(5)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = soup.findAll('div', class_='ace-field-value')
    total_cases = str(data[0].text).replace(",", "").replace("\n", "")
    total_deaths = int(str(data[1].text).replace(",", "").replace("\n", "")) + int(str(data[2].text).replace(",", "").replace("\n", ""))

    print(f'total_cases: {total_cases}')
    print(f'total_deaths: {total_deaths}')
    #
    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = total_cases
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = total_deaths
    print("Done Scraping guernsey\n")
    return df

def romania(driver, df):
    country = 'ROMANIA'
    st.write("Scraping romania...")
    from datetime import datetime, timedelta
    yesterday = datetime.now() - timedelta(1)
    d = datetime.strftime(yesterday, '%d')

    url = f'https://www.ms.ro/wp-content/uploads/2022/10/Buletin-de-presa-{d}.{month}.{year}.pdf'
    download_pdf(url)
    text = ''
    with pdfplumber.open(f'pdfs/Buletin-de-presa-{d}.{month}.{year}.pdf') as pdf:
        for page in pdf.pages:
            text += page.extract_text()

    cases = re.search('TOTAL (.+?)\n', text).group(1)
    cases = (cases.split(" "))
    total_cases = cases[0].replace(",", "")
    new_cases = cases[1].replace(",", "")

    deaths = re.search('Până astăzi, (.+?) ', text).group(1)
    total_deaths = deaths.replace(".", "")

    newdeaths = re.search('INSP (.+?) ', text).group(1)
    new_deaths = newdeaths.replace(".", "")

    hospital = re.search('este de (.+?) ', text).group(1)
    hospital = hospital.replace(".", "")

    icu = re.search('sunt internate (.+?) ', text).group(1)
    icu = icu.replace(".", "")

    print(f"total_cases: {total_cases}")
    print(f"new_cases: {new_cases}")
    print(f"total_deaths: {total_deaths}")
    print(f"new_deaths: {new_deaths}")
    print(f"hospital: {hospital}")
    print(f"icu: {icu}")

    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = total_cases
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = total_deaths
    df.loc[df['ADM0NAME'] == country, ['CasesNew']] = new_cases
    df.loc[df['ADM0NAME'] == country, ['DeathsNew']] = new_deaths
    df.loc[df['ADM0NAME'] == country, ['hospital']] = hospital
    df.loc[df['ADM0NAME'] == country, ['ICU']] = icu

    return df

def download_pdf(url):
    from selenium.webdriver import Chrome, ChromeOptions
    import os

    path_loc = os.path.join(os.getcwd(), "pdfs")
    print(path_loc)
    options = ChromeOptions()
    options.add_argument("--headless")
    chrome_prefs = {
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True,
        "download.open_pdf_in_system_reader": False,
        "profile.default_content_settings.popups": 0,
        "download.default_directory": path_loc
    }
    options.add_experimental_option("prefs", chrome_prefs)
    driver_location = 'driver/chromedriver'
    driver2 = Chrome(executable_path=driver_location, chrome_options=options)

    # test by inserting a URL you know that will open up a PDF file
    driver2.get(url)
    time.sleep(40)

def russia(driver, df):
    country = 'RUSSIAN FEDERATION'
    st.write("Scraping russia...")
    url = f'https://xn--80aesfpebagmfblc0a.xn--p1ai/information/'
    driver.get(url)
    time.sleep(5)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = soup.findAll('h3', class_='cv-stats-virus__item-value')
    hospital = data[0].text.replace("\n", "").replace(" ", "")
    new_cases = data[3].text.replace("\n", "").replace(" ", "")
    new_cases = re.sub("[^0-9a-zA-Z]+", "", new_cases)
    new_deaths = data[5].text.replace("\n", "").replace(" ", "")
    total_cases = data[4].text.replace("\n", "").replace(" ", "")
    total_deaths = data[6].text.replace("\n", "").replace(" ", "")
    print(f"new_cases: {new_cases}")
    print(f"total_cases: {total_cases}")
    print(f"new_deaths: {new_deaths}")
    print(f"total_deaths: {total_deaths}")
    print(f"hospital: {hospital}")

    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = total_cases
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = total_deaths
    df.loc[df['ADM0NAME'] == country, ['CasesNew']] = new_cases
    df.loc[df['ADM0NAME'] == country, ['DeathsNew']] = new_deaths
    df.loc[df['ADM0NAME'] == country, ['hospital']] = hospital

    print("Done Scraping russia\n")
    return df

def croatia(driver, df):
    country = 'CROATIA'
    st.write("Scraping croatia...")
    url = f'https://www.koronavirus.hr/najnovije/35'
    driver.get(url)
    time.sleep(5)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = soup.findAll('div', class_='column')
    text = data[27].text

    new_cases = re.search('zabilježeno je (.+?) ', text).group(1)
    new_cases = new_cases.replace(".", "")

    total_cases = re.search('je zabilježeno (.+?) ', text).group(1)
    total_cases = total_cases.replace(".", "")

    total_deaths = re.search('kojih je (.+?) ', text).group(1)
    total_deaths = total_deaths.replace(".", "")

    new_deaths = re.search('Preminulo je (.+?) ', text).group(1)
    new_deaths = new_deaths.replace(".", "")

    if 'njima je ' in text:
        hospital = re.search('njima je (.+?) ', text).group(1)
    elif 'njima su ' in text:
        hospital = re.search('njima su (.+?) ', text).group(1)
    hospital = hospital.replace(".", "")

    icu = re.search('respiratoru (.+?) ', text).group(1)
    icu = icu.replace(".", "")

    print(f"total_cases: {total_cases}")
    print(f"new_cases: {new_cases}")
    print(f"total_deaths: {total_deaths}")
    print(f"new_deaths: {new_deaths}")
    print(f"hospital: {hospital}")
    print(f"icu: {icu}")

    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = total_cases
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = total_deaths
    df.loc[df['ADM0NAME'] == country, ['CasesNew']] = new_cases
    df.loc[df['ADM0NAME'] == country, ['DeathsNew']] = new_deaths
    df.loc[df['ADM0NAME'] == country, ['hospital']] = hospital
    df.loc[df['ADM0NAME'] == country, ['ICU']] = icu

    return df


def greece(driver, df):
    country = 'GREECE'
    st.write("Scraping greece...")
    url = f'https://eody.gov.gr/category/covid-19/'
    driver.get(url)
    time.sleep(5)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = soup.findAll('div', class_='articles-container')
    data = data[0].findAll('a')
    links = []
    for i in data:
        if 'evdomadiaia-ekthesi-epitirisis-covid' in str(i['href']):
            links.append(i['href'])
    driver.get(links[0])
    time.sleep(5)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = soup.findAll('div', class_='main-container__inner paddingL')
    data = data[0].findAll('a')
    for i in data:
        if 'weekly-report' in str(i['href']):
            url = i['href']
    # prefix = 'https://eody.gov.gr/covid-gr-weekly-report-2022-'
    # suffix = links[0].split('-')[-1]
    # url = prefix+suffix
    download_pdf(url)
    text = ''
    list_of_files = glob.glob('pdfs/*')
    latest_file = max(list_of_files, key=os.path.getctime)
    with pdfplumber.open(latest_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    # print(text)
    new_cases = re.search('αναφοράς καταγράφηκαν (.+?) κρούσματα', text).group(1)
    new_cases = (new_cases.replace(".", ""))

    total_cases = re.search('απότηνέναρξητηςπανδημίαςανέρχεταισε(.+?)εκτωνοποίων', text).group(1)
    total_cases = (total_cases.replace(".", ""))

    total_deaths = re.search('καταγραφείσυνολικά(.+?)θάνατοι', text).group(1)
    total_deaths = total_deaths.replace(".", "")

    new_deaths = re.search('εβδομάδα αναφοράς καταγράφηκαν (.+?) θάνατοι', text).group(1)
    new_deaths = new_deaths.replace(".", "")

    icu = re.search('αναφοράςείναι(.+?)\(', text).group(1)
    icu = icu.replace(".", "")

    print(f"total_cases: {total_cases}")
    print(f"new_cases: {new_cases}")
    print(f"total_deaths: {total_deaths}")
    print(f"new_deaths: {new_deaths}")
    print(f"icu: {icu}")

    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = total_cases
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = total_deaths
    df.loc[df['ADM0NAME'] == country, ['CasesNew']] = new_cases
    df.loc[df['ADM0NAME'] == country, ['DeathsNew']] = new_deaths
    df.loc[df['ADM0NAME'] == country, ['ICU']] = icu

    return df

def hungary(driver, df):
    country = 'HUNGARY'
    st.write("Scraping hungary...")
    url = f'https://koronavirus.gov.hu/hirek'
    driver.get(url)
    time.sleep(5)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = soup.findAll('div', class_='article-teaser')
    links = []
    for i in data:
        # print(i.find('a')['href'])
        links.append(i.find('a')['href'])
    prefix = 'https://koronavirus.gov.hu/'
    url = prefix + links[1]
    print(url)
    driver.get(url)
    time.sleep(5)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = soup.findAll('div', class_='page_body')
    data = data[0].findAll('p')
    text = str(data[1])

    new_cases = re.search('héten összesen (.+?) új', text).group(1)
    new_cases = (new_cases.replace(" ", ""))
    new_cases = re.sub("[^0-9a-zA-Z]+", "", new_cases)

    total_cases = re.search('kezdete óta összesen (.+?) főre', text).group(1)
    total_cases = (total_cases.replace(" ", ""))
    total_cases = re.sub("[^0-9a-zA-Z]+", "", total_cases)

    new_deaths = re.search('héten elhunyt (.+?) többségében', text).group(1)
    new_deaths = new_deaths.replace(" ", "")
    new_deaths = re.sub("[^0-9a-zA-Z]+", "", new_deaths)

    total_deaths = re.search('elhunytak száma (.+?) főre', text).group(1)
    total_deaths = total_deaths.replace(" ", "")
    total_deaths = re.sub("[^0-9a-zA-Z]+", "", total_deaths)

    hospital = re.search('Jelenleg (.+?) koronavírusos', text).group(1)
    hospital = hospital.replace(" ", "")
    hospital = re.sub("[^0-9a-zA-Z]+", "", hospital)

    icu = re.search('kórházban, közülük(.+?)-', text).group(1)
    icu = icu.replace(" ", "").replace("-", "")
    icu = re.sub("[^0-9a-zA-Z]+", "", icu)


    print(f"total_cases: {total_cases}")
    print(f"new_cases: {new_cases}")
    print(f"total_deaths: {total_deaths}")
    print(f"new_deaths: {new_deaths}")
    print(f"hospital: {hospital}")
    print(f"icu: {icu}")

    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = total_cases
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = total_deaths
    df.loc[df['ADM0NAME'] == country, ['CasesNew']] = new_cases
    df.loc[df['ADM0NAME'] == country, ['DeathsNew']] = new_deaths
    df.loc[df['ADM0NAME'] == country, ['hospital']] = hospital
    df.loc[df['ADM0NAME'] == country, ['ICU']] = icu

    return df

def iceland(driver, df):
    country = 'ICELAND'
    st.write("Scraping iceland...")
    url = f'https://e.infogram.com/2dcfc49a-f2ed-40bb-bb8a-7e85a664157f?src=embed&parent_url=https%3A%2F%2Fwww.covid.is%2Fdata'
    driver.get(url)
    time.sleep(5)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    data = soup.findAll('div', class_='igc-textual-text innertext')
    total_cases = (data[-1].text.replace(" ", ""))
    total_cases = re.search('(.+?)confirmed', total_cases).group(1)

    data = soup.findAll('tr')
    row = []
    for i in data[-1]:
        row.append(i)
    total_deaths = row[1].text

    print(f"total_cases: {total_cases}")
    print(f"total_deaths: {total_deaths}")

    df.loc[df['ADM0NAME'] == country, ['CasesTotal']] = total_cases
    df.loc[df['ADM0NAME'] == country, ['DeathsTotal']] = total_deaths

    return df

def main():
    failed = []
    df = pd.read_csv('webmining_template.csv')
    driver = prep_driver()
    load_page_comps(driver)
    try:
        df = albania(driver, df)
    except Exception as e:
        print(e)
        failed.append('albania')
    try:
        df = russia(driver, df)
    except Exception as e:
        print(e)
        failed.append('russia')
    try:
        df = kosovo(driver, df)
    except Exception as e:
        print(e)
        failed.append('kosovo')
    try:
        df = greece(driver, df)
    except Exception as e:
        print(e)
        failed.append('greece')
    try:
        df = andorra(driver, df)
    except Exception as e:
        print(e)
        failed.append('andorra')
    try:
        df = bulgaria(driver, df)
    except Exception as e:
        print(e)
        failed.append('bulgaria')
    try:
        df = monaco(driver, df)
    except Exception as e:
        print(e)
        failed.append('monaco')
    try:
        df = serbia(driver, df)
    except Exception as e:
        print(e)
        failed.append('serbia')
    try:
        df = denmark(driver, df)
    except Exception as e:
        print(e)
        failed.append('denmark')
    try:
        df = sanmarino(driver, df)
    except Exception as e:
        print(e)
        failed.append('sanmarino')
    try:
        df = slovakia(driver, df)
    except Exception as e:
        print(e)
        failed.append('slovakia')
    try:
        df = turkey(driver, df)
    except Exception as e:
        print(e)
        failed.append('turkey')
    try:
        df = belgium(driver, df)
    except Exception as e:
        print(e)
        failed.append('belgium')
    try:
        df = malta(driver, df)
    except Exception as e:
        print(e)
        failed.append('malta')
    try:
        df = poland(driver, df)
    except Exception as e:
        print(e)
        failed.append('poland')
    try:
        df = norway(driver, df)
    except Exception as e:
        print(e)
        failed.append('norway')
    try:
        df = germany(driver, df)
    except Exception as e:
        print(e)
        failed.append('germany')
    try:
        df = jersey(driver, df)
    except Exception as e:
        print(e)
        failed.append('jersey')
    try:
        df = ireland(driver, df)
    except Exception as e:
        print(e)
        failed.append('ireland')
    try:
        df = guernsey(driver, df)
    except Exception as e:
        print(e)
        failed.append('guernsey')
    try:
        df = romania(driver, df)
    except Exception as e:
        print(e)
        failed.append('romania')
    try:
        df = croatia(driver, df)
    except Exception as e:
        print(e)
        failed.append('croatia')
    try:
        df = hungary(driver, df)
    except Exception as e:
        print(e)
        failed.append('hungary')
    try:
        df = iceland(driver, df)
    except Exception as e:
        print(e)
        failed.append('iceland')
    # df.to_csv(f'output_{today}.csv', index=False)
    st.write(f"FAILED COUNTRIES: {failed}")
    st.dataframe(df)
    csv = convert_df(df)
    st.download_button(
        "Download",
        csv,
        f"output_{today}",
        "text/csv",
        key='download-csv'
    )
    # france(driver)




# if __name__ == "__main__":
#     main()

def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

st.title("Daily web scraping")
if st.button('Scape the data'):
    main()
