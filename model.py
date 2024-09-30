from __future__ import annotations
import collections
from typing import Dict, Any, Callable
from urllib.parse import urlparse

from selenium.common import NoSuchElementException
from transliterate import translit
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import logging
from selenium.webdriver.common.by import By

# setting driver for parsing
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
options = Options()
options.headless = True
options.add_argument("--window-size=1920,1200")
options.add_argument('--disable-blink-features=AutomationControlled')
driver = webdriver.Chrome(options=options)


class SearchCandidates(Dict[str, Any]):
    ''' Parses work.ua and robota.ua to find list of top-candidates links according to searching criteria:
    site, category, profession, city, skills'''
    data = {
            "site": "",
            "category": "",
            "profession": "",
            "city": "",
            "skills": [],
    }
    transliterate_func: Callable[[str], str]
    create_base_list: Callable[[str], list[str]]
    find_cv_info_args: str

    def __init__(self, **kwargs: Any) -> None:
        ''' initialises class obj parameters according to chosen site
        kwars: dict() from bot
        :return obj  '''
        super().__init__(self.data)
        self.data.update(kwargs)
        if self.data['site'] == 'robota.ua':
            self.transliterate_func = self.make_translit_robota_ua
            self.create_base_list = self.create_base_list_robota_ua
        elif self.data['site'] == 'work.ua':
            self.transliterate_func = self.make_translit_work_ua
            self.create_base_list = self.create_base_list_work_ua

    @staticmethod
    def make_translit_work_ua(word: str) -> str:
        '''Return a str name of 'city' parameter after translation from ukr to en
        to make a valid link for parsing work.ua'''
        word = translit(word, 'uk', reversed=True).lower()
        if "'" in word:
            word = word.replace("'", "")
        if "ju" in word:
            word = word.replace("ju", "yu")
        if word.endswith("ij"):
            word = word.replace("ij", "iy")
        if word.endswith("ja"):
            word = word.replace("ja", "ya")
        if " " in word:
            word = word.replace(" ", "_")
        if "yi" in word:
            word = word.replace("yi", "i")
        if word == 'odessa':
            word = 'odesa'
        if word == 'mykolaiv':
            word = 'mykolaiv_nk'
        if word == 'chernivtsi':
            word = ''
        if word == '/skip':
            word = ""
        return word

    @staticmethod
    def make_translit_robota_ua(word: str) -> str:
        '''Return a str name of 'city' parameter after translation from ukr to en
              to make a valid link for parsing robota.ua'''
        word = translit(word, 'uk', reversed=True).lower()
        if "'" in word:
            word = word.replace("'", "")
        if "ju" in word:
            word = word.replace("ju", "yu")
        if word.endswith("ij"):
            word = word.replace("ij", "iy")
        if word.endswith("ja"):
            word = word.replace("ja", "ya")
        if "yi" in word:
            word = word.replace("yi", "i")
        if word == '/skip':
            word = "ukraine"
        return word

    @property
    def base_link(self) -> str:
        '''Return a link to pars site html with candidates list'''
        city = self.transliterate_func(self.data['city'])
        urls_categories = [
            ('Іт', 'https://robota.ua/candidates/all/zaporizhia?rubrics=%5B%221%22%5D',
             'https://www.work.ua/resumes-other-it/'),
            ('Наука/освіта', 'https://robota.ua/candidates/all/zaporizhia?rubrics=%5B%2210%22%5D',
             'https://www.work.ua/resumes-other-education-scientific/'),
            ('Маркетинг', 'https://robota.ua/candidates/all/zaporizhia?rubrics=%5B%2224%22%5D',
             'https://www.work.ua/resumes-other-marketing-advertising-pr/'),
            ('Медицина', 'https://robota.ua/candidates/all/zaporizhia?rubrics=%5B%229%22%5D',
             'https://www.work.ua/resumes-other-healthcare/'),
            ('Робочі спеціальності',
             'https://robota.ua/candidates/all/zaporizhia?rubrics=%5B%2220%22%5D',
             'https://www.work.ua/resumes-other-production-engineering/'),
            ('Торгівля', 'https://robota.ua/candidates/all/zaporizhia?rubrics=%5B%2217%22%5D',
             'https://www.work.ua/resumes-other-sales/'),
            ('Інжинери/технологи', 'https://robota.ua/candidates/all/zaporizhia?rubrics=%5B%2232%22%5D',
             'https://www.work.ua/resumes-other-production-engineering/'),
            ('Краса/спорт', 'https://robota.ua/candidates/all/zaporizhia?rubrics=%5B%228%22%2C%227%22%5D',
             'https://www.work.ua/resumes-other-beauty-sports/'),
            ('Ресторани/туризм', 'https://robota.ua/candidates/all/zaporizhia?rubrics=%5B%228%22%2C%2223%22%5D',
             'https://www.work.ua/resumes-other-hotel-restaurant-tourism/'),
            ('Логістика/склад', 'https://robota.ua/candidates/all/zaporizhia?rubrics=%5B%225%22%5D',
             'https://www.work.ua/resumes-other-logistic-supply-chain/'), ]
        category = self.data["category"]
        links = [(c, '{0}://{1}{2}?{3}'.format(urlparse(r).scheme, urlparse(r).netloc,
                                               urlparse(r).path.replace('zaporizhia', city), urlparse(r).query),
                  '{0}://{1}{2}'.format(urlparse(w).scheme, urlparse(w).netloc,
                                        urlparse(w).path).replace('other', city).replace('--', '-'))
                 for c, r, w in urls_categories if c == category]
        if self.data['site'] == 'robota.ua':
            return links[0][1]
        elif self.data['site'] == 'work.ua':
            return links[0][2]

    def create_base_list_robota_ua(self) -> list[str]:
        '''Return list of candidates links after parsing robota.ua '''
        print("Create base list robota.ua")
        urls = [self.base_link.replace('?', f'?page={n}&') for n in range(2, 10)]
        urls.append(self.base_link)
        profession = self.data["profession"]
        urls = [self.base_link, *urls]
        page_urls = []
        for url in urls:
            driver.get(url)
            try:
                links = driver.find_elements(By.XPATH,
                                             '/html/body/app-root/div/alliance-cv-list-page/main/article/'
                                             'div/div/alliance-employer-cvdb-cv-list/div/div'
                                             '/alliance-employer-cvdb-cv-list-card/section/div/'
                                             'alliance-shared-link-wrapping/a')
                for link in links:
                    text = link.text.split('\n')
                    if re.search(profession, text[0], flags=re.IGNORECASE):
                        page_url = link.get_attribute('href')
                        page_urls.append(page_url)
            except NoSuchElementException:
                logging.warning("No link!")
                break
        return page_urls

    def create_base_list_work_ua(self) -> list[str]:
        '''Return list of candidates links after parsing work.ua '''
        print("Create base list work.ua")
        page_urls = []
        urls = [f'{self.base_link}?page={n}' for n in range(2, 100)]
        print(urls)
        urls = [self.base_link, *urls]
        for url in urls:
            driver.get(url)
            for n in range(1, 11):
                try:
                    link = driver.find_element(By.XPATH, f'/html/body/main/div[2]/div/div[3]/div[2]'
                                                         f'/div[3]/div[{n}]/div[1]/h2/a')
                    page_url = link.get_attribute('href')
                    print(page_url)
                    if re.search(self.data['profession'], link.text, flags=re.IGNORECASE):
                        page_urls.append(page_url)
                except NoSuchElementException:
                    logging.warning("No link!")
        return page_urls

    @property
    def candidates_from_link(self) -> list[str]:
        '''sets attribute candidates_from_list with list of links
        according to chosen parameters except "skills"'''
        return self.create_base_list()

    @property
    def candidates_from_cv(self) -> list[str]:
        '''sets attribute candidates_from_cv with list of links according to chosen "skills"
                return fierst 5 link after ranking'''
        cv = self.candidates_from_link
        list_for_ranking = []
        for candidate_link in cv:
            try:
                driver.get(candidate_link)
            except NoSuchElementException:
                logging.warning("No addInfo!")
            finally:
                if self.data['site'] == 'robota.ua':
                    cv_info = driver.find_elements(By.TAG_NAME, 'alliance-cv-detail-page')
                else:
                    cv_info = driver.find_elements(By.ID, 'addInfo')
                for info in cv_info:
                    # adding link as many times, as there is the skill in list
                    # for further ranking according to frequency of link in list of cv
                    for skill in self.data['skills']:
                        if re.search(skill, info.text, flags=re.IGNORECASE):
                            list_for_ranking.append(candidate_link)
        ranking_cv = [link for link, rank in collections.Counter(list_for_ranking).most_common(5)]
        return ranking_cv

    def __repr__(self):
        '''Returns 5 cv after ranking in the case of getting chosen skills
        if not returns first 5 cv '''
        return f'Категорія: {self.data["category"]},\nМісто: {self.data["city"]}' \
               f'\nПрофіесія: {self.data["profession"]} ' \
               f'\nНайкращі кандидати: \n{self.candidates_from_cv}' \
            if len(self.candidates_from_cv) > 0 \
            else f'Категорія: {self.data["category"]},\nМісто: {self.data["city"]}, ' \
                 f'\nПерші 5 кандидатів: {self.candidates_from_link[:5]}'

