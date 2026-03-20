import requests
from bs4 import BeautifulSoup
import pandas as pd
def get_swim_links(url):
    # Add a user-agent to avoid being blocked by the server
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.37'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links that contain 'results' or specific event patterns
        # Based on the page structure, event links are often inside <a> tags
        links = soup.find_all('a', href=True)
        
        unique_links = {}
        for link in links:
            href = link['href']
            text = link.get_text(strip=True)
            
            # Filter for event-specific paths (usually numeric IDs in results)
            if '/286121?' in href and 'Swimoff' not in text:
                full_url = f"https://www.swimcloud.com{href}" if href.startswith('/') else href
                unique_links[text] = full_url
        
        return unique_links
    else:
        print(f"Failed to retrieve page: {response.status_code}")
        return {}
def find_scoring_events(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.37'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    # find the table that contains the prelims results
    prelims_header = soup.find('div', string=lambda t: t and 'Preliminaries' in t)
    if prelims_header is None:
        return {0: 'No prelims'}
    table = prelims_header.find_next('table')
    rows = table.find_all('tr')[1:]  # Skip the header row

    # Specific ranks to fetch (1-based index)
    target_ranks = [8, 16, 24]
    results = {}
    for rank in target_ranks:
        # rows[rank-1] handles the 0-based index of the list
        cells = rows[rank-1].find_all('td')
        name = cells[0].get_text(strip=True)
        time = cells[2].get_text(strip=True)
        results[rank] = time
    return results
# The URL from your shared context
meet_url = "https://www.swimcloud.com/results/286121/"
results = get_swim_links(meet_url)

table = pd.DataFrame()
# create a table with the from find_scoring_events and results
for event, link in results.items():
    print(f"{event}: {link}")
    results = find_scoring_events(link)
    print(results)
    # map event to the results
    table[event] = results
print(table)

