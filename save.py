import urllib.request
import re
from bs4 import BeautifulSoup
import urllib.parse
import datetime
from bs4.element import ResultSet
from sql import Controller

class Save():
    def __init__(self, top_url: str, dbname: str, table: str) -> None:
        self.top_url = top_url
        self.table = table
        self.controller = Controller(dbname)
        self.controller.create_table(
            table = table,
            sql = f'CREATE TABLE {self.table}(id INTEGER PRIMARY KEY, tweet TEXT NOT NULL, date DATETIME NOT NULL, retweet INTEGER NOT NULL)'
        )

    def create_bs(self, url: str) -> BeautifulSoup:
        while True:
            try:
                return BeautifulSoup(
                    urllib.request.urlopen(urllib.request.Request(
                        url = url, 
                        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106",}
                    ))
                    .read()
                    .decode('utf-8','ignore'),"lxml"
                )
            except Exception as e:
                print(e)
                return None

    def get_totalnum(self) -> int:
        return int(re.search(r'(^.*/p:)(\d+)', self.create_bs(self.top_url).select_one('.last > a:nth-child(1)').attrs['href'])[2])

    def generate_url(self) -> list:
        return list(map(lambda n: self.top_url + f'p:{n+1}', range(self.get_totalnum())))

    def get_tweet(self, url: str) -> None:
        [self.set_dev(x) for x in list(self.create_bs(url).find_all('div', {'class': 'tweet'}))]

    def set_dev(self, div: ResultSet):
        self.controller.do_execute(
            f"INSERT INTO {self.table} (date, tweet, retweet) VALUES (?, ?, ?)",
            (
                datetime.datetime.strptime(div.find_all('div', {'class': 'posted-at'})[0].text, '%Y年%m月%d日 %H:%M:%S'),
                div.find_all('p', {'class': 'text'})[0].text,
                1 if len(div.find_all('div', {'class': 'profile-image-box'})[0].find_all('span')) >= 1 else 0
            )
        )

    def main(self) -> None:
        [self.get_tweet(x) for x in self.generate_url()]

print("URL:")
url = input()
print("Database name:")
dbname = input()
print("Table name")
table = input()
save = Save(url, dbname, table)
save.main()