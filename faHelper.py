import http.cookiejar
import re
import sys
import urllib.request
import time
import os
import threading
import queue
from urllib.error import HTTPError

from bs4 import BeautifulSoup
from tabulate import tabulate
import codecs
import warnings

from selenium import webdriver

WORKERS = 4         # Mutli-Thread workers
MAX_RETRY = 3       # Number of retries for HTML requests
SLEEP_TIME = 20     # Wait time when robot is detected


# From October 12, 2015 to 20151012
def change_date_string(date_bad):
    date = date_bad.split(" ")
    date[0] = date[0].replace("January", "01")
    date[0] = date[0].replace("February", "02")
    date[0] = date[0].replace("March", "03")
    date[0] = date[0].replace("April", "04")
    date[0] = date[0].replace("May", "05")
    date[0] = date[0].replace("June", "06")
    date[0] = date[0].replace("July", "07")
    date[0] = date[0].replace("August", "08")
    date[0] = date[0].replace("September", "09")
    date[0] = date[0].replace("October", "10")
    date[0] = date[0].replace("November", "11")
    date[0] = date[0].replace("December", "12")
    date[1] = date[1].replace(",", "")

    if len(date[1]) == 1:
        date[1] = "0" + date[1]

    date_good = date[2] + date[0] + date[1]
    return date_good


class FAhelper:
    """Clase para ayudar a bajar la informacion de filmaffinity"""

    # FA URL set.
    url_login = "https://filmaffinity.com/en/account.ajax.php?action=login"  # New login URL?
    url_votes = "http://www.filmaffinity.com/en/myvotes.php"  # URL used to get total votes and pages
    url_votes_id = "https://www.filmaffinity.com/en/userratings.php?user_id="  # URL to dump user ratings
    url_votes_id_page_suffix = "&p="  # Prefix for ulr to get specific page
    url_film = "http://www.filmaffinity.com/en/film"  # Movie page URL to get detailed info
    url_film_suffix = ".html"  # End of URL for movie page

    urlVotes_prefix = "http://www.filmaffinity.com/en/myvotes.php?p="
    urlVotes_sufix = "&orderby="

    urlMain = "http://www.filmaffinity.com/en/main.php"

    cookiejar = None
    web_session = None

    fa_movies = []
    fa_movies_filled = []

    def __init__(self):
        self.user_name = ""
        self.user_pass = ""
        self.user_id = "0"

        # Enable cookie support for urllib2
        self.cookiejar = http.cookiejar.CookieJar()
        self.web_session = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookiejar))

    def get_movies_dumped(self):
        return self.fa_movies

    def get_filled_movies_dumped(self):
        return self.fa_movies_filled

    def set_user(self, user_name, user_pass):
        self.user_name = user_name
        self.user_pass = user_pass

    def get_user(self):
        return self.user_name, self.user_pass

    def set_user_id(self, user_id):
        self.user_id = str(user_id)

    # returns value of film affinity user ID
    def get_user_id(self):
        return self.user_id

    def login(self):
        user, password = self.get_user()

        self.web_session.open(self.url_login)

        data_form = {"postback": 1, "rp": "", "username": user,
                     "password": password}

        f = urllib.parse.urlencode(data_form)
        f = f.encode('utf-8')

        req = urllib.request.Request(self.url_login, f)
        self.web_session.open(req)  # Our cookiejar automatically receives the cookies, after the request

        # Web to read number of votes
        web_response = self.web_session.open(self.url_votes)

        pattern = re.compile('\?user_id=(\d+)"')
        match = pattern.search(web_response.read().decode('utf-8'))

        if match:
            user_id = match.group(1)
        else:
            print(
                "ERROR FOUND: change regular expression at FAhelper.login() for user ID. Probably FA changed web page "
                "structure")
            sys.exit("Error happens, check log.")

        self.user_id = user_id

    # returns 1 when login is succeed
    def login_succeed(self):
        return len(self.cookiejar) > 1

    def get_num_votes(self):

        if self.user_id == "0":
            print("ERROR FOUND: No user id found. Please login or set user id.")
            sys.exit("Error happens, check log.")

        url = self.url_votes_id + self.user_id

        try:
            web_response = self.web_session.open(url)
            html = web_response.read().decode('utf-8')

        except HTTPError as e:
            self.solve_robot(url)

        num_pages = 0
        soup_page = BeautifulSoup(html, 'html.parser')
        pages_div = soup_page.body.findAll('div', attrs={'class': 'pager'})
        for page in pages_div:
            for link in page.findAll('a'):
                if link.string.isnumeric():
                    if int(link.string) > int(num_pages):
                        num_pages = int(link.string)

        num_votes = 0
        for div in soup_page.body.findAll('div', attrs={'class': 'number'}):
            i = div.findAll('i', attrs={'class': 'fa fa-ratings-fa'})
            if i:
                if div.text.replace(",", "").isnumeric():
                    num_votes = int(div.text.replace(",", ""))

        return num_votes, num_pages

    def do_dump_votes_page(self, page):

        if self.user_id == "0":
            print("ERROR FOUND: No user id found. Please login or set user id.")
            return

        url = self.url_votes_id + str(self.user_id) + self.url_votes_id_page_suffix + str(page)

        web_response = self.web_session.open(url)
        html = web_response.read().decode('utf-8')
        # html = str(html, 'utf-8')

        intento = 0

        # Check if FA has blocked
        if "<title>Too many request</title>" in html:
            self.solve_robot(url)
            web_response = self.web_session.open(url)
            html = web_response.read().decode('utf-8')

            if web_response.getcode() != 200:
                intento = intento + 1

        soup_page = BeautifulSoup(html, 'html.parser')
        days_div = soup_page.body.findAll('div', attrs={'class': 'user-ratings-wrapper'})

        num_movies_at_page = 0

        for day_div in days_div:

            # Get day when the vote was done:
            day = day_div.find('div', attrs={'class': 'user-ratings-header'})
            day_bad_format = day.text.replace("Rated on ", "")
            day_yyyymmdd = change_date_string(day_bad_format)

            # Each day may have more than one movie:
            rates = day_div.findAll('div', attrs={'class': 'user-ratings-movie fa-shadow'})
            for movie in rates:

                # Get filmaffinity ID
                try:
                    movie_id = movie.find('div', attrs={'class': 'movie-card movie-card-1'}).get("data-movie-id")
                except AttributeError:
                    movie_id = "000000"

                # Get movie personal rate
                try:
                    movie_rate = movie.find('div', attrs={'class': 'ur-mr-rat'}).text
                except AttributeError:
                    movie_rate = -1

                # Get movie filmaffinity rate
                try:
                    movie_fa_rate = movie.find('div', attrs={'class': 'avgrat-box'}).text
                except AttributeError:
                    movie_fa_rate = -1

                # Get movie filmaffinity votes
                try:
                    movie_fa_votes = movie.find('div', attrs={'class': 'ratcount-box'}).text
                except AttributeError:
                    movie_fa_votes = -1

                # Get title div
                title_div = movie.find('div', attrs={'class': 'mc-title'})

                # But before, get movie country
                img_div = title_div.find('img', alt=True)
                movie_country = img_div['alt']

                # Get title div
                pattern = re.compile('\((\d\d\d\d)\)')
                match = pattern.search(title_div.text)
                if match:
                    movie_year = match.group(1)
                    movie_title = title_div.text.replace("(" + movie_year + ")", "").strip()
                    movie_title = movie_title.replace("(TV Series)", "").strip()
                    movie_title = movie_title.replace("(TV)", "").strip()
                    movie_title = movie_title.replace("(S)", "").strip()
                else:
                    print(
                        "ERROR FOUND: change regular expression at FAhelper.do_dump_votes_page() for movie year. "
                        "Probably FA changed web page structure")
                    sys.exit("Error happens, check log.")

                movie_result = FAMovieData(movie_id=movie_id, movie_title=movie_title, movie_year=movie_year,
                                                movie_rate=movie_rate, vote_day_yyyymmdd=day_yyyymmdd)

                movie_result.set_movie_details(movie_fa_rate=movie_fa_rate, movie_fa_votes=movie_fa_votes,
                                               movie_country=movie_country, movie_director=None, movie_cast=None,
                                               movie_genre=None, movie_duration=None, movie_synopsis=None)

                self.fa_movies.append(movie_result)

                num_movies_at_page = num_movies_at_page + 1

        return page, num_movies_at_page

    def complete_movie_detailed_info(self, movie):

        movie_id = movie.get_id()

        found = False
        intento = 0
        while not found:
            if intento < MAX_RETRY:
                movie_url = self.url_film + str(movie_id) + self.url_film_suffix
                try:
                    web_response = self.web_session.open(movie_url)
                    html = web_response.read().decode('utf-8')

                except HTTPError as e:
                    self.solve_robot(movie_url)

                    intento = intento + 1
                    continue

                if web_response.getcode() != 200:
                    print(web_response.getcode())

                    intento = intento + 1
                    continue

                # Check if FA has blocked
                if "<title>Too many request</title>" in html:
                    self.solve_robot(movie_url)
                    web_response = self.web_session.open(movie_url)

                    html = web_response.read().decode('utf-8')
                    if web_response.getcode() != 200:
                        intento = intento + 1
                        continue

                # Get movie title information
                soup_page = BeautifulSoup(html, 'html.parser')
                title_tag = soup_page.body.find('h1', attrs={'id': 'main-title'})

                if title_tag is None:
                    print((
                            "ERROR FOUND: change regular expression at getMovieInfoById() for movie title. Probably "
                            "FA changed web page structure. Movie ID: " + str(
                        movie_id)))
                    intento = intento + 1
                    continue

                else:
                    movie_title = title_tag.text
                    movie_title = movie_title.replace("(TV Series)", "").strip()
                    movie_title = movie_title.replace("(TV)", "").strip()
                    movie_title = movie_title.replace("(S)", "").strip()
                    found = True

                # Get movie year information
                year_tag = soup_page.body.find('dd', attrs={'itemprop': 'datePublished'})

                if year_tag == None:
                    print((
                            "ERROR FOUND: change regular expression at getMovieInfoById() for movie year. Probably FA "
                            "changed web page structure. Movie ID: " + str(
                        movie_id)))
                    intento = intento + 1
                    continue

                else:
                    movie_year = year_tag.text

                # Get movie country information
                country_tag = soup_page.body.find('span', attrs={'id': 'country-img'})
                country_image_tag = country_tag.find('img', alt=True)

                if (country_tag is None) | (country_image_tag is None):
                    print((
                            "ERROR FOUND: change regular expression at getMovieInfoById() for movie county. Probably "
                            "FA changed web page structure. Movie ID: " + str(
                        movie_id)))
                else:
                    movie_country = country_image_tag['alt']

                # Get movie director information
                movie_director = ""
                director_tag = soup_page.body.find('dd', attrs={'class': 'directors'})

                if director_tag is None:
                    print((
                            "ERROR FOUND: change regular expression at getMovieInfoById() for movie director. "
                            "Probably FA changed web page structure. Movie ID: " + str(
                        movie_id)))

                else:
                    try:
                        movie_director = director_tag.text
                    except AttributeError:
                        movie_director = ""

                    # clean the string
                    movie_director = movie_director.strip()

                    while '  ' in movie_director:
                        movie_director = movie_director.replace('  ', ' ')
                        movie_director = movie_director.replace('\n', '')
                        movie_director = movie_director.replace('\r', '')

                # Get movie cast information
                cast_tag = soup_page.body.find('span', attrs={'itemprop': 'actor'})

                try:
                    movie_cast = cast_tag.parent.text
                except AttributeError:
                    movie_cast = ""

                # clean the string
                movie_cast = movie_cast.strip()
                while '  ' in movie_cast:
                    movie_cast = movie_cast.replace('  ', ' ')
                    movie_cast = movie_cast.replace('\n', '')
                    movie_cast = movie_cast.replace('\r', '')

                # Get movie genre infomration
                genre_tags = soup_page.body.find('span', attrs={'itemprop': 'genre'})

                try:
                    movie_genre = genre_tags.parent.text
                except AttributeError:
                    movie_genre = ""

                # clean the string
                movie_genre = movie_genre.strip()
                while '  ' in movie_genre:
                    movie_genre = movie_genre.replace('  ', ' ')
                    movie_genre = movie_genre.replace('\n', '')
                    movie_genre = movie_genre.replace('\r', '')

                # Get movie duration information
                duration_tag = soup_page.body.find('dd', attrs={'itemprop': 'duration'})
                try:
                    movie_duration = duration_tag.text
                except AttributeError:
                    movie_duration = ""

                # Get movie synopsis  information
                synopsis_tag = soup_page.body.find('dd', attrs={'itemprop': 'description'})
                try:
                    movie_synopsis = synopsis_tag.text
                    movie_synopsis = movie_synopsis.replace('  ', ' ')
                    movie_synopsis = movie_synopsis.replace('\n', '')
                    movie_synopsis = movie_synopsis.replace('\r', '')
                except AttributeError:
                    movie_synopsis = ""

        movie_result = FAMovieData(movie_id=movie_id,
                                    movie_title=movie_title,
                                    movie_year=movie_year,
                                    movie_rate=movie.get_rate(),
                                    vote_day_yyyymmdd=movie.get_rate_day_yyyymmdd()
                                    )

        movie_result.set_movie_details(movie_fa_rate=movie.get_fa_rate(),
                                       movie_fa_votes=movie.get_fa_votes(),
                                       movie_country=movie_country,
                                       movie_director=movie_director,
                                       movie_cast=movie_cast,
                                       movie_genre=movie_genre,
                                       movie_duration=movie_duration,
                                       movie_synopsis=movie_synopsis
                                       )

        movie.set_movie_details(movie.get_fa_rate(),
                                movie.get_fa_votes(),
                                movie_country=movie_country,
                                movie_director=movie_director,
                                movie_cast=movie_cast,
                                movie_genre=movie_genre,
                                movie_duration=movie_duration,
                                movie_synopsis=movie_synopsis
                                )

        return movie_result

    def get_dump_all_votes(self):
        num_votes, num_pages = self.get_num_votes()

        num_pages_print = num_pages
        if num_pages_print == 0:
            num_pages_print = 1
        print(("FOUND: {0} movies in {1} pages.".format(num_votes, num_pages_print)))

        # First get all possible information from vote list
        queue_basic = queue.Queue()
        for i in range(WORKERS):
            # FaVoteDumper(queue, self).start() # start a worker
            worker = FaVotePageDumper(queue_basic, self)
            worker.setDaemon(True)
            worker.start()

        for page in range(1, int(num_pages) + 1):
            queue_basic.put(page)

        if int(num_pages) == 0:
            queue_basic.put(1)
        print("All pages pushed to queue!")

        for i in range(WORKERS):
            queue_basic.put(None)  # add end-of-queue markers

        # Wait all threats of queue to finish
        queue_basic.join()

        queue_fill = queue.Queue()
        for i in range(WORKERS):
            # FaFillInfo(queueFill, self).start() # start a worker
            worker = FaGetMovieDetails(queue_fill, self)
            worker.setDaemon(True)
            worker.start()

        for movie in self.fa_movies:
            # print "Push movie: ", movie[0]
            queue_fill.put(movie)
        print("\r\nAll movies pushed to queue to get all movie information.")

        for i in range(WORKERS):
            queue_fill.put(None)  # add end-of-queue markers

        # Wait all threats of queueFill to finish
        queue_fill.join()

    @staticmethod
    def check_robot_solver_requirements():
        dir_path = os.path.dirname(os.path.realpath(__file__))
        driver_filename = dir_path + '\chromedriver.exe'

        if os.path.isfile(driver_filename):
            print('Chromedriver found (OK)')
        else:
            warnings.warn("Chromedriver NOT found. Used for solving robot challenge.")
            warnings.warn('Driver expected path: ' + driver_filename)

    def solve_robot(self, url):

        dir_path = os.path.dirname(os.path.realpath(__file__))
        driver_filename = dir_path + "\chromedriver.exe"

        driver = webdriver.Chrome(driver_filename)
        driver.get(url)

        warnings.warn("Script on hold: Waiting to solve robot challenge")

        while 1:
            time.sleep(SLEEP_TIME)

            try:
                web_response = self.web_session.open(url)
                html = web_response.read().decode('utf-8')

            except HTTPError as e:
                continue

            # Check if FA has blocked
            if "<title>Too many request</title>" not in html:
                break


class FaVotePageDumper(threading.Thread):
    def __init__(self, pages_queue, fa_handler):
        self.__pages_queue = pages_queue
        threading.Thread.__init__(self)
        self.fa_handler = fa_handler

    def run(self):
        while 1:
            page = self.__pages_queue.get()
            if page is None:
                self.__pages_queue.task_done()
                break  # reached end of queue

            page, num_movies_at_page = self.fa_handler.do_dump_votes_page(page)
            print('Analyzed vote page: {0} found {1} movies'.format(page, num_movies_at_page))

            self.__pages_queue.task_done()


class FaGetMovieDetails(threading.Thread):
    def __init__(self, movies_queue, fa_handler):
        self.__movies_queue = movies_queue
        threading.Thread.__init__(self)
        self.fa_handler = fa_handler

    def run(self):
        while 1:
            film = self.__movies_queue.get()
            if film is None:
                self.__movies_queue.task_done()
                break  # reached end of queue

            movie_with_details = self.fa_handler.complete_movie_detailed_info(film)
            self.fa_handler.fa_movies_filled.append(movie_with_details)

            print('FaGetMovieDetails: {0} ({1}) get all data. Remaining: {2}'.format(
                movie_with_details.get_title(), movie_with_details.get_id(), self.__movies_queue.qsize() - 1))
            self.__movies_queue.task_done()


class FAMovieData:

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

    def get_id(self):
        return self.movie_id

    def get_title(self):
        return self.movie_title

    def get_year(self):
        return self.movie_year

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

    @staticmethod
    def get_column_names():
        column_names = (
            "ID", "Title", "Year", "Vote", "Voted", "FA rate", "FA votes", "Country", "Director", "Cast", "Genre",
            "Duration", "Synopsis")

        return column_names

    def tabulate1(self):
        return self.movie_id, self.movie_title, self.movie_year, self.movie_rate, self.vote_day_yyyymmdd, \
               self.movie_fa_rate, self.movie_fa_votes, self.movie_country, self.movie_director, self.movie_cast, \
               self.movie_genre, self.movie_duration, self.movie_synopsis

    def __repr__(self):
        s = "[FAMovieData CLASS] Title: {0}, Year: {1}, ID: {2}, Rated: {3} on {4}, FA rate {5}, FA votes {6}, " \
            "duration: {7}, Country: {8} Director: {9}, Cast: {10}, Genre: {11}, Synopsis {12}".format(
            self.movie_title, self.movie_year, self.movie_id, self.movie_rate, self.vote_day_yyyymmdd,
            self.movie_fa_rate, self.movie_fa_votes, self.movie_duration, self.movie_country,
            self.movie_director, self.movie_cast, self.movie_genre, self.movie_synopsis)

        # return s.encode('ascii', 'backslashreplace')  # No idea about original intent of this line
        return s

    def __str__(self):
        s = "Title: {0}, Year: {1}, ID: {2}, Rated: {3} on {4}, FA rate {5}, FA votes {6}, duration: {7}, " \
            "Country: {8} Director: {9}, Cast: {10}, Genre: {11}, Synopsis {12}".format(self.movie_title,
                                                                                        self.movie_year,
                                                                                        self.movie_id,
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

        # return s.encode('ascii', 'backslashreplace')  # No idea about original intent of this line
        return s


class FAMovieList:
    def __init__(self):
        self.__movie_table = []

    def __len__(self):
        return len(self.__movie_table)

    def empty(self):
        return len(self.__movie_table) < 1

    def append(self, movie):
        assert isinstance(movie, FAMovieData)
        self.__movie_table.append(movie)

    def save_report(self, file_name):
        movie_table_tabulated = []
        for movie in self.__movie_table:
            assert isinstance(movie, FAMovieData)
            movie_table_tabulated.append(movie.tabulate1())
        table_acii = tabulate(movie_table_tabulated,
                              headers=list(FAMovieData.get_column_names()),
                              tablefmt='orgtbl')

        table_file = codecs.open(file_name, "w", "utf_16")
        table_file.write(table_acii)
        table_file.close()

        return table_acii

    def save_csv(self, file_name):

        csv = ''
        header = ''

        fields = FAMovieData.get_column_names()
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
