import sys
import time
import http.cookiejar
import urllib.request
import re
from selenium import webdriver
from difflib import SequenceMatcher
from bs4 import BeautifulSoup
import json
from tabulate import tabulate
import codecs

WORKERS = 4  # MultiThread workers
MAX_RETRY = 10
SUCCEED = 99  # Magic number used for retries


def save_to_file(what, file_name):
    f = open(file_name, "wb")
    f.write(what)
    f.close()


class ImdbHelper:
    """Clase para ayudar a bajar la informacion de imdb"""

    # IMDB URL set.
    imdb_login_url = 'https://secure.imdb.com/register-imdb/login#'
    imdb_search_url = 'https://www.imdb.com/find'
    imdb_movie_url = 'https://www.imdb.com/title/'
    imdb_post_vote_url = 'https://www.imdb.com/ratings/_ajax/title'

    cookiejar = None
    web_session = None

    def __init__(self):
        self.user_name = ""
        self.user_pass = ""
        self.user_id = ""

        # Enable cookie support for urllib2
        self.cookiejar = http.cookiejar.CookieJar()
        self.web_session = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookiejar))

    def set_user(self, user_name, user_pass):
        self.user_name = user_name
        self.user_pass = user_pass

    def get_user(self):
        return self.user_name, self.user_pass

    def set_user_id(self, user_id):
        self.user_id = str(user_id)

    def do_login(self):
        attempt = 0
        while attempt < MAX_RETRY:
            try:
                web_response = self.web_session.open(self.imdb_login_url)
                break
            except:
                attempt = attempt + 1

        if attempt == MAX_RETRY:
            print("ERROR FOUND: Connection failed at imdbHelper.login()")
        else:

            html = web_response.read().decode('utf-8')
            pattern = re.compile('<a href="(https:\/\/www.imdb.com\/ap\/signin\?[\w\W]+?)"')

            ulr_imdb_login = pattern.search(html).group(1)

            driver = webdriver.Chrome()
            driver.get(ulr_imdb_login)

            time.sleep(5)
            search_box = driver.find_element_by_name('email')
            search_box.send_keys(self.user_name)
            search_box = driver.find_element_by_name('password')
            search_box.send_keys(self.user_pass)
            search_box.submit()

            time.sleep(5)

            cookies = driver.get_cookies()
            for cookie in cookies:
                c = http.cookiejar.Cookie(version=0,
                                          name=cookie['name'],
                                          value=cookie['value'],
                                          port='80',
                                          port_specified=False,
                                          domain=cookie['domain'],
                                          domain_specified=True,
                                          domain_initial_dot=False,
                                          path=cookie['path'],
                                          path_specified=True,
                                          secure=cookie['secure'],
                                          expires=cookie['expiry'],
                                          discard=False,
                                          comment=None,
                                          comment_url=None,
                                          rest=None,
                                          rfc2109=False)
                self.cookiejar.set_cookie(c)
            driver.close()
            driver.quit()

    # returns 1 when login is succeed
    def login_succeed(self):
        return 'session-token' in [cookie.name for cookie in self.cookiejar]

    def search_movie_id(self, target_title, target_year):

        # No idea why there is \x00
        # TODO: check origin of \x00
        target_title = target_title.replace('\x00', '')
        target_year = target_year.replace('\x00', '')

        find_list = []

        intento = 0
        while intento < MAX_RETRY:
            try:

                data_form = {'ref_': 'nv_sr_sm', 'q': target_title.encode('utf-8')}
                f = urllib.parse.urlencode(data_form)
                f = f.encode('utf-8')

                # Force headers language to get titles in English
                headers = {"Accept-Language": "en-US,en;q=0.5"}

                req = urllib.request.Request(url=self.imdb_search_url, data=f, headers=headers)

                # Cookiejar automatically receives the cookies, after the request
                web_response = self.web_session.open(req)

                intento = SUCCEED

            except:
                intento = intento + 1

                if intento >= MAX_RETRY and intento != SUCCEED:
                    print(("ERROR FOUND: Connection failed at ImdbHelper.search_movie_id() - " + mTitle + "(" + mYear +
                           ")"))
                    return ImdbFoundMovie(result=ImdbFoundMovie.RESULT_BAD_MATCH)

        url_after_search = web_response.url

        web_response_raw = web_response.read()
        response_html = web_response_raw.decode('utf-8')

        # save_to_file(web_response_raw, "imdb_search_result")

        # Check if IMDB has already redirect to movie
        if url_after_search.find('/title/tt') != -1:

            movie_id = url_after_search[url_after_search.find('/title/tt') + len('/title/tt')
                                        - 2:url_after_search.find('/title/tt') + len('/title/tt') + 7]
            pattern = re.compile(
                'itemprop="name">([\W\w]*?)<\/span>[\n\w\W]*?<span class="nobr">[\n\w\W]*?\(<a href="[\w\W]+?>(\d+)<\/a>')

            match = pattern.search(response_html)
            try:
                movie_title = match.group(1)
                movie_title = movie_title.replace("\n", "")
            except:
                movie_title = "Not Found"
            try:
                movie_year = match.group(2)
                movie_year = movie_year.replace("\n", "")
            except:
                movie_year = "0"

            return ImdbFoundMovie(movie_id, movie_title, movie_year)

        # When not redirect to movie page a list is shown
        else:

            pattern = re.compile('"result_text"> <a href="\/title\/(tt\d+).*?>(.+?)<\/a>.*?\((\d+)\)',
                                 re.MULTILINE | re.DOTALL)
            iterator = re.finditer(pattern, response_html)

            for movie_result in iterator:

                movie_id = str(movie_result.group(1))
                movie_year = movie_result.group(3)
                movie_title = movie_result.group(2)

                bad_capture = movie_title.find(';">')
                while bad_capture != -1:
                    movie_title = movie_title[bad_capture + 3:]
                    bad_capture = movie_title.find(';">')

                title_ratio = SequenceMatcher(None, target_title.encode('utf8'), movie_title.encode('utf8')).ratio()
                # print("TARGET TITLE: '" + target_title + "' Found Title: '" + movie_title + "' RATIO: " + str(title_ratio))

                movie = ImdbFoundMovie(id=movie_id, title=movie_title, year=movie_year, ratio=title_ratio)
                find_list.append(movie)
                # print(movie)

            # Get the best match
            best_result = ImdbFoundMovie(ratio=0, result=ImdbFoundMovie.RESULT_NO_MATCH)

            for movie in find_list:

                if abs(int(movie.get_year()) - int(target_year)) <= 1:
                    if best_result.get_ratio() < movie.get_ratio():
                        best_result = movie

            if best_result.get_ratio() > 0.5:
                # print("GOOD RESULT: " + str(best_result))
                return best_result
            else:
                # print("RESULT_BAD_MATCH")
                return ImdbFoundMovie(result=ImdbFoundMovie.RESULT_BAD_MATCH)

    def vote_movie(self, movie_code, movie_vote):
        url_movie = self.imdb_movie_url + movie_code + "/"
        web_response = self.web_session.open(url_movie)

        web_response_raw = web_response.read()
        response_html = web_response_raw.decode('utf-8')

        # save_to_file(web_response_raw, "imdb_page")

        soup_page = BeautifulSoup(response_html, 'html.parser')

        rating_widget = soup_page.find(id='star-rating-widget')
        auth_hash = rating_widget['data-auth']

        data_post = {'tconst': movie_code,
                     'rating': movie_vote,
                     'auth': auth_hash,
                     'tracking_tag': 'title-maindetails',
                     'pageId': movie_code,
                     'pageType': 'title',
                     'subpageType': 'main'
                     }

        f = urllib.parse.urlencode(data_post)
        f = f.encode('utf-8')

        try:
            req = urllib.request.Request(url=self.imdb_post_vote_url, data=f)
            self.web_session.open(req)  # Our cookiejar automatically receives the cookies, after the request

            return 1
        except:
            return -1

    def get_movie_vote(self, movie_code):
        url_movie = self.imdb_movie_url + movie_code + "/"
        web_response = self.web_session.open(url_movie)

        web_response_raw = web_response.read()
        response_html = web_response_raw.decode('utf-8')

        # save_to_file(web_response_raw, "imdb_page")

        soup_page = BeautifulSoup(response_html, 'html.parser')

        # All this information is easy to read:
        # scripts = soup_page.find_all("script", type="application/ld+json")
        # for s in scripts:
        # js = json.loads("".join(s.contents))

        # print(js['name'])
        # print(js['genre'])
        # print(js['description'])
        # print(js['datePublished'])
        # print(js['keywords'])
        # print(js['aggregateRating']['ratingValue'])
        # print(js['director']['name'])

        rate_span = soup_page.body.findAll('span', attrs={'class': 'star-rating-value'})

        if rate_span is None or len(rate_span) == 0:
            # print("No rate found for: " + movie_code)
            return '0'

        else:
            # print("Rate for " + movie_code + ": " + rate_span[0].text)
            return rate_span[0].text


class ImdbFoundMovie:
    RESULT_MATCH = 'match'
    RESULT_NO_MATCH = 'no_match'
    RESULT_BAD_MATCH = 'bad_match'

    def __init__(self, id=None, title=None, year=None, ratio=None, result=RESULT_MATCH):
        if result != self.RESULT_MATCH:
            if id is not None:
                pass
            assert id is None
            assert title is None
            assert year is None
            if result == self.RESULT_BAD_MATCH:
                assert ratio == None
        self.__id = id
        self.__title = title
        self.__year = year
        self.__ratio = ratio
        self.__result = result
        pass

    def __repr__(self):
        s = "<ImdbFoundMovie Title: {0}, Year: {1}, Ratio: {2} Result: {3}, Code: {4}>".format(self.__title,
                                                                                               self.__year,
                                                                                               self.__ratio,
                                                                                               self.__result,
                                                                                               self.__id)
        return s

    def __str__(self):
        s = "Title: {0}, Year: {1}, Ratio: {2} Result: {3}, Code: {4}".format(self.__title, self.__year,
                                                                              self.__ratio, self.__result,
                                                                              self.__id)
        return s

    def get_result(self):
        return self.__result

    def get_id(self):
        return self.__id

    def get_id_decoded(self):
        return self.__id.decode()

    def get_title(self):
        return self.__title

    def get_year(self):
        return self.__year

    def get_ratio(self):
        return self.__ratio

    def is_no_match(self):
        return self.__result == self.RESULT_NO_MATCH

    def is_bad_match(self):
        return self.__result == self.RESULT_BAD_MATCH


# This class is same as FAMovieData but adding IMDB code and IMDB title
# TODO: Improve this class + Think better architecture
class FAMovieDataExtra:

    def __init__(self, movie_id, movie_title, movie_year, movie_rate, vote_day_yyyymmdd):
        self.movie_id = movie_id
        self.movie_title = movie_title
        self.movie_year = movie_year
        self.movie_rate = movie_rate
        self.vote_day_yyyymmdd = vote_day_yyyymmdd

        self.movie_fa_rate = None
        self.movie_fa_votes = None
        self.movie_country = None
        self.movie_director = None
        self.movie_cast = None
        self.movie_genre = None
        self.movie_duration = None
        self.movie_synopsis = None

        self.imdb_id = None
        self.imdb_tittle = None
        self.imdb_year = None

    def set_movie_details(self, movie_fa_rate, movie_fa_votes, movie_country, movie_director, movie_cast,
                          movie_genre, movie_duration, movie_synopsis):
        self.movie_fa_rate = movie_fa_rate
        self.movie_fa_votes = movie_fa_votes
        self.movie_country = movie_country
        self.movie_director = movie_director
        self.movie_cast = movie_cast
        self.movie_genre = movie_genre
        self.movie_duration = movie_duration
        self.movie_synopsis = movie_synopsis

    def set_imdb_details(self, imdb_id, imdb_tittle, imdb_year):
        self.imdb_id = imdb_id
        self.imdb_tittle = imdb_tittle
        self.imdb_year = imdb_year

    def get_id(self):
        return self.movie_id

    def get_imdb_id(self):
        return self.imdb_id

    def get_title(self):
        return self.movie_title

    def get_imdb_title(self):
        return self.imdb_tittle

    def get_year(self):
        return self.movie_year

    def get_imdb_year(self):
        return self.imdb_year

    def get_rate(self):
        return self.movie_rate

    def get_rate_day_yyyymmdd(self):
        return self.vote_day_yyyymmdd

    def get_fa_rate(self):
        return self.movie_fa_rate

    def get_fa_votes(self):
        return self.movie_fa_votes

    def get_country(self):
        return self.movie_country

    def get_director(self):
        return self.movie_director

    def get_cast(self):
        return self.movie_cast

    def get_genre(self):
        return self.movie_genre

    def get_duration(self):
        return self.movie_duration

    def get_synopsis(self):
        return self.movie_synopsis

    @staticmethod
    def get_column_names():
        column_names = (
            "FA_ID", "IMDB_ID", "FA_Title", "IMDB_Title", "FA_Year", "FA_Year", "Vote", "Voted", "FA rate", "FA votes",
            "Country", "Director", "Cast", "Genre",
            "Duration", "Synopsis")

        return column_names

    def tabulate1(self):
        return self.movie_id, self.imdb_id, self.movie_title, self.imdb_tittle, self.movie_year, self.imdb_year, \
               self.movie_rate, self.vote_day_yyyymmdd, \
               self.movie_fa_rate, self.movie_fa_votes, self.movie_country, self.movie_director, self.movie_cast, \
               self.movie_genre, self.movie_duration, self.movie_synopsis

    def __repr__(self):
        s = "[FAMovieDataExtra CLASS] Title: {0}, Year: {1}, ID: {2}, Title_IMDB: {3}, Year_IMDB: {4}, ID_IMDB: {5}, " \
            "Rated: {6} on {7}, FA rate {8}, FA votes {9}, duration: {10}, Country: {11} Director: {12}, Cast: {13}, " \
            "Genre: {14}, Synopsis {15}".format(self.movie_title,
                                                self.movie_year,
                                                self.movie_id,
                                                self.imdb_tittle,
                                                self.imdb_year,
                                                self.imdb_id,
                                                self.movie_rate,
                                                self.vote_day_yyyymmdd,
                                                self.movie_fa_rate,
                                                self.movie_fa_votes,
                                                self.movie_duration,
                                                self.movie_country,
                                                self.movie_director,
                                                self.movie_cast,
                                                self.movie_genre,
                                                self.movie_synopsis)
        return s

    def __str__(self):
        s = "Title: {0}, Year: {1}, ID: {2}, Title_IMDB: {3}, Year_IMDB: {4}, ID_IMDB: {5}, " \
            "Rated: {6} on {7}, FA rate {8}, FA votes {9}, duration: {10}, Country: {11} Director: {12}, Cast: {13}, " \
            "Genre: {14}, Synopsis {15}".format(self.movie_title,
                                                self.movie_year,
                                                self.movie_id,
                                                self.imdb_tittle,
                                                self.imdb_year,
                                                self.imdb_id,
                                                self.movie_rate,
                                                self.vote_day_yyyymmdd,
                                                self.movie_fa_rate,
                                                self.movie_fa_votes,
                                                self.movie_duration,
                                                self.movie_country,
                                                self.movie_director,
                                                self.movie_cast,
                                                self.movie_genre,
                                                self.movie_synopsis)
        return s


class FAMovieExtraList:
    def __init__(self):
        self.__movie_table = []

    def __len__(self):
        return len(self.__movie_table)

    def empty(self):
        return len(self.__movie_table) < 1

    def append(self, movie):
        assert isinstance(movie, FAMovieDataExtra)
        self.__movie_table.append(movie)

    def get_movies(self):
        return self.__movie_table

    def save_report(self, file_name):
        movie_table_tabulated = []
        for movie in self.__movie_table:
            assert isinstance(movie, FAMovieDataExtra)
            movie_table_tabulated.append(movie.tabulate1())
        table_ascii = tabulate(movie_table_tabulated,
                               headers=list(FAMovieDataExtra.get_column_names()),
                               tablefmt='orgtbl')

        table_file = codecs.open(file_name, "w", "utf_16")
        table_file.write(table_ascii)
        table_file.close()

        return table_ascii

    def save_csv(self, file_name):

        csv = ''
        header = ''

        fields = FAMovieDataExtra.get_column_names()
        for f in fields:
            header = header + str(f) + ';'

        csv = csv + header + '\n'

        for movie in self.__movie_table:
            for a in movie.tabulate1():
                if a is None:
                    a = ""
                if isinstance(a, int):
                    a = str(a)
                a = a.replace(";", ",")
                csv = csv + a + ";"
            csv = csv + "\n"

        csv_file = codecs.open(file_name, "w", "utf_16")
        csv_file.write(csv)
        csv_file.close()

        return csv
