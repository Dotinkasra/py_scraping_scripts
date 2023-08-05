from bs4 import BeautifulSoup
import requests, sqlite3, glob, re, base64, time

class Fc2cm():
    def __init__(self) -> None:
        self.dirs: list = [
            base64.b64decode("L1ZvbHVtZXMvVkNfTWVkaWEyL+WLleeUuy9mYzIvKioK").decode().replace('\n', ''),
            base64.b64decode("L1ZvbHVtZXMvVkNfTWVkaWEzL01vdmllcy9GQzIvKioK").decode().replace('\n', ''),
            base64.b64decode("L1ZvbHVtZXMvVkNfTWVkaWEzL01vdmllcy9GQzIvaDI2NC8qKgo=").decode().replace('\n', ''),
        ]
        self.db = self.Fc2Db()
        self.bs = self.Scraper()

    def get_filenames_to_list(self) -> list:
        result = []
        for target_dir in self.dirs:
            files = glob.glob(target_dir)
            for file in files:
                sep_file = file.split('/')
                [result.append(fc2file) for fc2file in list(filter(None, sep_file)) if self.is_saved_fc2_video_dir(fc2file)]
        return result

    def is_saved_fc2_video_dir(self, dirname: str) -> bool:
        pattern = re.compile(r'FC2-PPV-[0-9]+')
        result = pattern.match(dirname)
        return True if result else False
    
    def extract_fc2_id(self, dirname: str) -> int:
        pattern = re.compile(r'FC2-PPV-([0-9]+)')
        result = pattern.match(dirname)
        if not result:
            return None
        return int(result.group(1))
    
    def get_fc2_id_list(self) -> list:
        return sorted(list(filter(None, [self.extract_fc2_id(x) for x in self.get_filenames_to_list()])))

    def differ_currentry_and_db(self) -> list:
        return list(set(self.get_fc2_id_list()).difference(self.db.select_all()))
    
    def fetch_video_info(self, id: int|str) -> tuple:
        soup = self.bs.fetch_fc2cm(id)
        return (id, self.bs.extract_video_title(soup), self.bs.extract_video_contributor(soup))

    def regist_video_info(self, id: int|str):
        self.db.insert_video_info(*self.fetch_video_info(id))
    
    class Fc2Db():
        def select_all(self) -> list:
            sql: str = f"SELECT id FROM fc2"
            with sqlite3.connect("./fc2.db") as conn:
                cur = conn.cursor()
                result: list = cur.execute(sql).fetchall()
                cur.close()
                return sorted([r[0] for r in result])
        
        def exists_id(self, id: int|str):
            sql: str = f"SELECT id FROM fc2 WHERE id = ?"
            with sqlite3.connect("./fc2.db") as conn:
                cur = conn.cursor()
                result: list = cur.execute(sql, (str(id))).fetchall()
                cur.close()
                if result and len(result) > 0:
                   return True
                return False    
            
        def insert_video_info(self, id: int|str, title: str, contributor: str):
            sql: str = f"INSERT INTO fc2(id, name, title, contributor) VALUES(?, ?, ?, ?)"
            param: tuple = (id, f"FC2-PPV-{id}", title, contributor)
            print(param)
            with sqlite3.connect("./fc2.db") as conn:
                cur = conn.cursor()
                cur.execute(sql, param)
                conn.commit()
                cur.close()

    class Scraper():

        def fetch_fc2cm(self, id: int|str) -> BeautifulSoup:
            domain = base64.b64decode("aHR0cHM6Ly9mYzJjbS5jb20vCg==").decode().replace('\n', '')
            uri = f"{domain}?p={str(id)}&nc=0"
            user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
            header = {
                    "User-Agent": user_agent,
                    "referer" : domain,
                    "Accept-Language": "ja;q=0.7"
            }
            response = requests.get(uri, headers=header)
            return BeautifulSoup(response.text, 'lxml')
        
        def extract_video_title(self, soup: BeautifulSoup) -> str:
            return soup.find('title').text
        
        def extract_video_contributor(self, soup: BeautifulSoup) -> str:
            return soup.find_all('table')[1].select_one('h2 > a').text 

for video in fc2.differ_currentry_and_db():
    fc2.regist_video_info(video)
    time.sleep(3)

