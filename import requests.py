import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

url = "https://www.swimphone.com/meets/event_order.cfm?smid=20293"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

all_events = []
def time_to_seconds(time_str):
    """
    Convert a string like "2:22.66" or "52.34" to total seconds as float
    """
    if not time_str or time_str in ['DQ', 'NT']:
        return None  # handle missing or invalid times
    
    if ':' in time_str:
        mins, secs = time_str.split(':')
        return float(mins) * 60 + float(secs)
    else:
        return float(time_str)
tables = soup.find_all('table')
def get_psych_table(link):
    response = requests.get(link, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the first table with tbody
    table = soup.find('table')
    tbody = table.find('tbody') if table else None
    if not tbody:
        return pd.DataFrame(columns=['Rank','Name','Seed Time'])
    # iterate over the rows of the table and extract the rank, name, and time
    data = []
    for row in tbody.find_all('tr'):
        cells = row.find_all('td')
        rank = cells[0].get_text(strip=True)
        name = cells[3].get_text(strip=True)
        time = cells[4].get_text(strip=True)
        data.append([rank, name, time])
    return pd.DataFrame(data, columns=['Rank','Name','Seed Time'])
def get_prelims_table(link):
    # print("prelims link", link)
    response = requests.get(link, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')
    tbody = table.find('tbody') if table else None
    if not tbody:
        return pd.DataFrame(columns=['Rank','Name','Seed Time'])
    data = []
    for row in tbody.find_all('tr'):
        cells = row.find_all('td')
        if cells[0].get_text(strip=True) == '':
            continue
        time = cells[5].get_text(strip=True)
        data.append([time])
    return pd.DataFrame(data, columns=['PrelimsTime'])
for table in tables:
    # Check if table is prelims by seeing if any <th> contains "Prelims"
    th_texts = [th.get_text(strip=True) for th in table.find_all('th')]
    if any("Prelims" in text for text in th_texts):
        # Loop over rows (skip header)
        for row in table.find_all('tr')[1:]:
            cells = row.find_all('td')
            if len(cells) < 4 or cells[5].find('a') is None:
                continue  # skip totals or empty rows
            
            event_num = cells[0].get_text(strip=True)
            sex = cells[1].get_text(strip=True)
            distance = cells[2].get_text(strip=True)
            stroke = cells[3].get_text(strip=True)
            psych_link = cells[5].find('a')['href']
            prelims_link = cells[8].find('a')['href']
            # print("prelims link", prelims_link)
            psych_table = get_psych_table(psych_link)
            prelims_table = get_prelims_table(prelims_link)
            psych_time = psych_table.iloc[19]['Seed Time']
            psych_time_10 = psych_table.iloc[9]['Seed Time']
            prelims_20th_time = prelims_table.iloc[19]['PrelimsTime']
            prelims_10th_time = prelims_table.iloc[9]['PrelimsTime']
            all_events.append({
                "Event #": event_num,
                "Sex": sex,
                "Race": distance+' '+stroke,
                "20th Seed": psych_time,
                "20th Prelims": prelims_20th_time,
                "20th Diff": time_to_seconds(prelims_20th_time) - time_to_seconds(psych_time),
                "10th Seed": psych_time_10,
                "10th Prelims": prelims_10th_time,
                "10th Diff": time_to_seconds(prelims_10th_time) - time_to_seconds(psych_time_10),
            })

df = pd.DataFrame(all_events)
print(df.describe())
print(df.head)