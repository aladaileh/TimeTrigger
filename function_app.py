import logging
import azure.functions as func 
from requests import Session
from datetime import datetime , date, timedelta
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from tools import send_email, create_custom_logger, upload_log_to_blob, take_and_leave_one, leave_and_take_one, get_translated_text
from scraping_code import eia_weekly_report, weather_scraping
from ice_price_scraping import ttf_price_scraping, nbp_price_scraping

app = func.FunctionApp()

@app.schedule(schedule="0 0 10 * *", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
@app.blob_output(arg_name="outputblob", path="gasconsumption/EIAWeeklyReport.csv", connection="AzureWebJobsStorage")
def EIAWeeklyReport(myTimer: func.TimerRequest, outputblob: func.Out[str]) :
    try:
        logger, log_stream = create_custom_logger('eia_weekly_logger')
    except Exception as e:
        raise ValueError('Null value detected in the data')
    try:
        new_row= eia_weekly_report(logger)
    except Exception as e:
        logger.error(str(e))
    try:
        updated_csv_content = new_row.to_csv()
        outputblob.set(updated_csv_content)
        logger.info('EIA weekly report processed and saved to blob successfully.')
        upload_log_to_blob('eia-weeklyreport',log_stream=log_stream)
    except Exception as e:
        logger.error(str(e))
        subject="Error in Code (EIA_weeklyreport)"
        send_email(subject=subject,body=log_stream.getvalue())


@app.schedule(arg_name="timer3", schedule= "0 0 16 * *",run_on_startup=True,
              use_monitor=False)
@app.blob_output(arg_name="outputblob", path="gasconsumption/weather.csv",
                  connection="AzureWebJobsStorage")
def weather(timer3: func.TimerRequest, outputblob: func.Out[str]):
    logger, log_stream = create_custom_logger('weather_logger')
    try:
        new_row = weather_scraping(logger)
        updated_csv_content = new_row.to_csv()
        outputblob.set(updated_csv_content)
        logger.info('Weather data processed and saved to blob successfully.')
    except Exception as e:
        logger.error(str(e))
        subject="Error in Code (Weather)"
        send_email(subject=subject,body=log_stream.getvalue())
    finally:
        upload_log_to_blob('weather',log_stream=log_stream)


@app.schedule(schedule="0 0 9 * *", arg_name="ttfTimer", run_on_startup=True,
              use_monitor=False) 
@app.blob_output(arg_name="outputblob", path="gasconsumption/TTFPrices.csv", connection="AzureWebJobsStorage")
def TTFPriceScraping(ttfTimer: func.TimerRequest, outputblob: func.Out[str]) :
    """Scrape Dutch TTF Natural Gas Futures prices"""
    try:
        logger, log_stream = create_custom_logger('ttf_price_logger')
    except Exception as e:
        raise ValueError('Logger initialization failed')
    
    try:
        new_data = ttf_price_scraping(logger)
        
        # Save to blob
        updated_csv_content = new_data.to_csv(index=False)
        outputblob.set(updated_csv_content)
        logger.info(f'TTF price data processed and saved to blob successfully. Rows: {len(new_data)}')
        upload_log_to_blob('ttf-prices', log_stream=log_stream)
        
    except Exception as e:
        logger.error(f"Error in TTF price scraping: {str(e)}")
        subject = "Error in Code (TTF Price Scraping)"
        send_email(subject=subject, body=log_stream.getvalue())
        raise


@app.schedule(schedule="0 30 9 * *", arg_name="nbpTimer", run_on_startup=True,
              use_monitor=False) 
@app.blob_output(arg_name="outputblob", path="gasconsumption/NBPPrices.csv", connection="AzureWebJobsStorage")
def NBPPriceScraping(nbpTimer: func.TimerRequest, outputblob: func.Out[str]) :
    """Scrape UK NBP Natural Gas Futures prices"""
    try:
        logger, log_stream = create_custom_logger('nbp_price_logger')
    except Exception as e:
        raise ValueError('Logger initialization failed')
    
    try:
        new_data = nbp_price_scraping(logger)
        
        # Save to blob
        updated_csv_content = new_data.to_csv(index=False)
        outputblob.set(updated_csv_content)
        logger.info(f'NBP price data processed and saved to blob successfully. Rows: {len(new_data)}')
        upload_log_to_blob('nbp-prices', log_stream=log_stream)
        
    except Exception as e:
        logger.error(f"Error in NBP price scraping: {str(e)}")
        subject = "Error in Code (NBP Price Scraping)"
        send_email(subject=subject, body=log_stream.getvalue())
        raise