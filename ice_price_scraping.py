from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import logging
from datetime import datetime
import time



def setup_driver():
    """Setup Chrome driver with Azure-compatible options"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--disable-software-rasterizer')
    return webdriver.Chrome(options=options)

def scrape_ice_futures(url, logger, market_name):
    """Generic function to scrape ICE futures data"""
    driver = None
    try:
        logger.info(f"Starting {market_name} scraping from {url}")
        driver = setup_driver()
        driver.get(url)
        
        # Wait for table to load
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="market-list"] table.table-bigdata')))
        time.sleep(3)  # Additional wait for data population
        
        # Parse HTML
        soup = BeautifulSoup(driver.page_source, "html.parser")
        table = soup.select_one('div[data-testid="market-list"] table.table-bigdata')
        
        if not table:
            raise ValueError(f"Table not found for {market_name}")
        
        # Extract headers
        headers = [th.text.strip() for th in table.select("thead th")]
        logger.info(f"Headers found: {headers}")
        
        # Extract data
        data = []
        for row in table.select("tbody tr"):
            cols = [td.text.strip() for td in row.select("td")]
            
            # Skip invalid rows
            if not cols or len(cols) != len(headers):
                continue
            if any(skip_word in str(cols[0]) for skip_word in ["Intraday", "Created with Highcharts", "Last Update"]):
                continue
                
            data.append(cols)
        
        if not data:
            raise ValueError(f"No valid data rows found for {market_name}")
            
        # Create DataFrame
        df = pd.DataFrame(data, columns=headers)
        logger.info(f"Successfully scraped {len(df)} rows for {market_name}")
        
        # Add metadata columns for database structure
        df['Source'] = 'ICE'
        df['Commodity'] = 'Natural Gas'
        df['Type'] = 'Futures'
        df['SubType'] = market_name
        df['AsOfDate'] = datetime.now()
        df['Timestamp'] = datetime.now()
        
        return df
        
    except Exception as e:
        logger.error(f"Error scraping {market_name}: {str(e)}")
        raise
    finally:
        if driver:
            driver.quit()

def convert_contract_to_date(contract_str):
    """Convert contract format (e.g., 'Aug25') to datetime"""
    if not contract_str or pd.isna(contract_str):
        return pd.NaT
    
    try:
        # Remove any extra spaces
        contract_str = contract_str.strip()
        
        # Dictionary for month abbreviations
        month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        # Extract month and year
        month_abbr = contract_str[:3]
        year_str = contract_str[3:]
        
        # Get month number
        month = month_map.get(month_abbr)
        if not month:
            return pd.NaT
            
        # Convert 2-digit year to 4-digit
        year = int('20' + year_str)
        
        # Create date (first day of the month)
        return pd.Timestamp(year=year, month=month, day=1)
        
    except Exception:
        return pd.NaT

def ttf_price_scraping(logger):
    """Scrape Dutch TTF Natural Gas Futures"""
    url = "https://www.ice.com/products/27996665/Dutch-TTF-Natural-Gas-Futures/data?marketId=5706224"
    df = scrape_ice_futures(url, logger, "TTF")
    
    # Map TTF-specific columns to standard structure
    df['Location'] = 'Netherlands'
    df['HubType'] = 'TTF'
    df['Period'] = 'hourly'  # Keep original contract name
    df['Unit'] = 'EUR/MWh'
    df['SubSubTybe'] = df.get('Contract', '')  # Put contract in SubSubTybe
    df['Senario'] = 'Actual'
    df['FreeText'] = ''
    
    # Extract price value
    df['Value'] = df.get('Last', '0')#.str.replace(',', '').astype(float)  # Adjust column name
    
    # Convert contract date to ValueDate
    df['ValueDate'] = df['Contract'].apply(convert_contract_to_date)
    
    # Remove rows where ValueDate is null/NaT or Value is null/0
    df = df.dropna(subset=['ValueDate', 'Value'])
    df = df[df['Value'] != 0]
    
    # Log any dropped rows
    logger.info(f"TTF data after removing nulls: {len(df)} rows")
    
    # Select only required columns
    required_cols = ['Location', 'Commodity', 'Period', 'Source', 'Senario', 
                     'Type', 'SubType', 'SubSubTybe', 'Unit', 'HubType', 
                     'FreeText', 'ValueDate', 'AsOfDate', 'Value', 'Timestamp']
    
    return df[required_cols]

def nbp_price_scraping(logger):
    """Scrape UK NBP Natural Gas Futures"""
    url = "https://www.ice.com/products/910/UK-NBP-Natural-Gas-Futures/data?marketId=5863515"
    df = scrape_ice_futures(url, logger, "NBP")
    
    # Map NBP-specific columns to standard structure
    df['Location'] = 'UK'
    df['HubType'] = 'NBP'
    df['Period'] = 'hourly'  # Keep original contract name
    df['Unit'] = 'GBP/therm'
    df['SubSubTybe'] = df.get('Contract', '')  # Put contract in SubSubTybe
    df['Senario'] = 'Actual'
    df['FreeText'] = ''
    
    # Extract price value
    df['Value'] = df.get('Last', '0')#.str.replace(',', '').astype(float)  # Adjust column name
    
    # Convert contract date to ValueDate
    df['ValueDate'] = df['Contract'].apply(convert_contract_to_date)
    
    # Remove rows where ValueDate is null/NaT or Value is null/0
    df = df.dropna(subset=['ValueDate', 'Value'])
    df = df[df['Value'] != 0]
    
    # Log any dropped rows
    logger.info(f"NBP data after removing nulls: {len(df)} rows")
    
    # Select only required columns
    required_cols = ['Location', 'Commodity', 'Period', 'Source', 'Senario', 
                     'Type', 'SubType', 'SubSubTybe', 'Unit', 'HubType', 
                     'FreeText', 'ValueDate', 'AsOfDate', 'Value', 'Timestamp']
    
    return df[required_cols]

