import pandas as pd
import requests
from io import StringIO

url = "https://www.swimphone.com/meets/swimmers.cfm?smid=20323"

# Use requests to fetch the HTML with a browser-like header
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/115.0 Safari/537.36"
}
response = requests.get(url, headers=headers)

# Now parse the HTML with pandas
tables = pd.read_html(StringIO(response.text))
# sort the table by club name
tables[0] = tables[0].sort_values(by="Club")
# get the number of swimmers in each club
club_counts = tables[0]['Club'].value_counts()
# print the club counts
print(club_counts)
# print the club names and the number of swimmers in each club
for club, count in club_counts.items():
    print(f"{club}: {count}")
# print the total number of swimmers
print(f"Total number of swimmers: {club_counts.sum()}")