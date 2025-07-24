
from requests import Session
import requests
from datetime import datetime 
import pandas as pd
from bs4 import BeautifulSoup
from tools import timetrigger_wrapper
import logging


def eia_weekly_report(logger)-> pd.DataFrame:    
    try:
        url = "https://ir.eia.gov/ngs/ngs.html"
        headers = {
            "Age": "20",
            "Cache-Control": "public, max-age=30",
            "Date": "Tue, 23 Jul 2024 11:30:02 GMT",
            "Via": "1.1 16f38d6df135d34d67fe44df60d91ab4.cloudfront.net (CloudFront)",
            "X-Amz-Cf-Id": "qQVBzdm5Jed8YQ_fOKtHolyveGuPEZ15M5igonZ-p672w1vYV-Oe3A==",
            "X-Amz-Cf-Pop": "LHR61-P1",
            "X-Cache": "Hit from cloudfront"
        }
        session = Session()
        session.headers.update(headers)
        r = session.get(url)
        res = r.content
        soup = BeautifulSoup(res, "html.parser")
    except Exception as e:
        logger.error(e)
    try:
        table = soup.find('table')
        last_row = table.find_all('tr')[-2]
        first_row = table.find_all('tr')[2]
        value = last_row.find_all('td')[1].get_text()
        Value = float(value.replace(',', ''))
        valuedate = first_row.find_all('td')[2].get_text().split()[2].strip("()")
        date_obj = datetime.strptime(valuedate, "%m/%d/%y")
        div_element = soup.find('div', class_='report_header')
        text_content = div_element.get_text()
        next_release_index = text_content.find("Next Release:")
        if next_release_index != -1:
            next_release_date = text_content[next_release_index:].split("Next Release:")[1].strip()
            AsOfDate = next_release_date.split(' ')[0] + ' ' + next_release_date.split(' ')[1] + ' ' + next_release_date.split(' ')[2]
            AsOfDate=datetime.strptime(AsOfDate, '%B %d, %Y')
        else:
            logger.info("Next Release information not found.")
    except Exception as e:
        logger.error(str(e))
    try:
        Value_Date = date_obj
        Commodity = 'Gas'
        location = 'USA'
        Period = 'Weekly'
        Source = 'EIA'
        Senario = 'Base'
        Unit = 'Bcf'
        Type = 'Storage'
        new_row = timetrigger_wrapper(Value_Date, AsOfDate, location, Commodity, Period, Source, Senario, Type, Value, Unit)
        return new_row
    except Exception as e:
        logger.error(str(e))

def weather_scraping(logger):
    try:
        url= requests.get('https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/dubai/2024-08-31/2024-09-15?unitGroup=metric&include=days&key=U629JFB7PKJB9U4JKYDMS7DPF&contentType=json')
        response= url.json()
    except Exception as e:
        logger.error(f'colud not returen the data from the url coz {str(e)}')
    try:
        days = response['days']
        df = pd.DataFrame(days)
        df = df.set_index(df['datetime'])
        weather = df['temp']
    except Exception as e:
        logger.error(f'{str(e)}')
    try:
        for i in weather:
            if isinstance(i, float):      
                pass
    except:
        logger.error('There is a problem with the data type')
    try:
        for i in pd.isnull(weather):
            if i:
                logger.error('There is a Null value')
        weather.index= pd.to_datetime(weather.index)
        Commodity = 'Weather'
        location = 'UAE'
        Period = 'Daily'
        Source = 'visualcrossing'
        Senario = 'Base'
        Unit = 'Degree'
        Type = 'tempreture'
        Value_Date = weather.index[-1].strftime('%Y-%m-%d')
        AsOfDate= weather.index[-1].strftime('%Y-%m-%d')
        Value= weather[-1]
        new_row = timetrigger_wrapper(Value_Date, AsOfDate, location, Commodity, Period, Source, Senario, Type, Value, Unit)
        return new_row
    except Exception as e:
        logger.error(str(e))


weather= weather_scraping(logging)
print(weather)