import os
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from azure.storage.blob import BlobServiceClient
import logging
import requests
from datetime import datetime 
import pandas as pd
import numpy as np

def upload_log_to_blob(function_name, log_stream):
        try:
            # Azure Blob Storage configurations
            AZURE_STORAGE_CONNECTION_STRING = os.getenv("AzureWebJobsStorage")
            BLOB_CONTAINER_NAME = f"{function_name}-log-container"  # Set the log container name
            BLOB_LOG_FILENAME = f"logs/log.log"  # Unique filename for the log
            
            # Create a BlobServiceClient using the connection string
            blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
            
            # Get the container client (create if doesn't exist)
            container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)
            try:
                container_client.create_container()
            except Exception as e:
                pass
            
            # Create the blob client and upload the log
            blob_client = container_client.get_blob_client(BLOB_LOG_FILENAME)
            log_content = log_stream.getvalue() 
            blob_client.upload_blob(log_content, overwrite=True)
        
        except Exception as e:
            logging.error(f"Failed to upload logs to Blob Storage: {str(e)}")

def create_custom_logger(logger_name):
    log_stream = io.StringIO()  
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    
    stream_handler = logging.StreamHandler(log_stream)
    stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    if not logger.handlers:
        logger.addHandler(stream_handler)
    
    return logger, log_stream



def send_email(subject,body):
    smtp_server='smtp.gmail.com'
    port=587
    recipients = ['aadylih@gmail.com']
    password='dkenpftyzirukknz'
    sender='ahmadriad19971@gmail.com'
    msg=MIMEMultipart()
    msg['From']= sender
    msg['To']=','.join(recipients)
    msg['Subject']=subject
    msg.attach(MIMEText(body,'Plain'))
    server=smtplib.SMTP(smtp_server,port)
    server.starttls()
    server.login(sender, password)
    server.send_message(msg)
    server.quit()
    


def get_translated_text(text):
    """
    Returns the translated text.
    """

    URL = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={text}".format(
        text=text
    )

    response = requests.get(URL)

    if response.status_code == 200:
        json_response = response.json()
        translated_text = json_response[0][0][0]

        return translated_text
    else:
        raise text #Exception("Failed to translate text: {}".format(response.status_code))
#%%%

def take_and_leave_one(input_list):
    result = []
    for i in range(0, len(input_list), 2):
        result.append(input_list[i])
    return result
def leave_and_take_one(input_list):
    result = []
    for i in range(1, len(input_list), 2):
        result.append(input_list[i])
    return result


def timetrigger_wrapper(Value_Date: np.datetime64, AsOfDate: np.datetime64, location: str, Commodity: str, 
                        Period: str, Source: str, Senario: str, Type: str, Value: float, Unit: str)-> pd.DataFrame:
    
    data = {
        'ValueDate': [Value_Date],
        'AsOfDate': [AsOfDate],
        'Location': [location],
        'Commodity': [Commodity],
        'Period': [Period],
        'Source': [Source],
        'Senario': [Senario],
        'Timestamp': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        'Type': [Type],
        'Value': [Value],
        'SubType': [np.nan],
        'SubSubType': [np.nan],
        'Unit': [Unit],
        'HubType': [np.nan],
        'FreeText': [np.nan]
    }

    new_row = pd.DataFrame(data)
    
    return new_row
