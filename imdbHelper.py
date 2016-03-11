# -*- coding: utf-8 -*-

import re
import sys
from difflib import SequenceMatcher as sDiff
from xml.dom import minidom

import cookielib
import urllib
import urllib2

WORKERS = 4  # Mutli-Thread workers
MAX_RETRY = 10


class IMDBhelper:
    """Clase para ayudar a bajar la informacion de imdb"""

    # IMDB URL set.
    IMDBurlLogin = "https://secure.imdb.com/register-imdb/login#"
    IMDBvotedPrefix = "http://www.imdb.com/user/ur5741926/ratings?start="
    IMDBvotedSufix = "&view=detail&sort=title:asc&defaults=1&my_ratings=restrict&scb=0.28277816087938845"
    IMDBakas = "http://akas.imdb.com/"
    IMDBbyTitleAPI = "http://www.imdb.com/xml/find?xml=1&nr=1&tt=on&"
    IMDBurlCaptcha = "https://secure.imdb.com/widget/captcha?type="

    def __init__(self):
        self.userName = ""
        self.userPass = ""

        # Enable cookie support for urllib2
        self.cookiejar = cookielib.CookieJar()
        self.webSession = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))

    def setUser(self, userName, userPass):
        self.userName = userName
        self.userPass = userPass

    def getUser(self):
        return self.userName, self.userPass

    def setUserID(self, userId):
        self.userId = str(userId)

    def login(self):
        intento = 0
        while intento < MAX_RETRY:
            try:
                webResponse = self.webSession.open(self.IMDBurlLogin)
                intento = 99
            except:
                intento = intento + 1
        if intento == MAX_RETRY:
            print("ERROR FOUND: Connection failed at imdbHelper.login()")
        else:
            html = webResponse.read()
            html = unicode(html, 'utf-8')

            # Get captcha URL
            pattern = re.compile('<img src="\/widget\/captcha\?type=([\w\W]+?)"')
            match = pattern.search(html)
            if match:
                captchaURL = self.IMDBurlCaptcha + match.group(1)
            else:
                print(
                    "ERROR FOUND: change regular expression at login() for checksum. Probably IMDB changed web page structure")
                sys.exit("Error happens, check log.")

            print("Type captcha form image: " + captchaURL)
            capcha = raw_input('>')

            pattern = re.compile('<input type="hidden" name="([\d\w]+)" value="([\d\w]+)" \/>')
            match = pattern.finditer(html)

            if match:
                for result in match:
                    chsm1 = result.group(1)
                    chsm2 = result.group(2)

                dataForm = {chsm1: chsm2, "login": self.userName, "password": self.userPass, "captcha_answer": capcha}
            else:
                print(
                    "ERROR FOUND: change regular expression at login() for checksum. Probably IMDB changed web page structure")
                sys.exit("Error happens, check log.")

            dataPost = urllib.urlencode(dataForm)
            request = urllib2.Request("https://secure.imdb.com/register-imdb/login#", dataPost)

            webResponse = self.webSession.open(request)  # Our cookiejar automatically receives the cookies

            if not 'id' in [cookie.name for cookie in self.cookiejar]:
                print("Login error!: Incorrect IMDB User or password, please try again.")

    # returns 1 when login is succeed
    def loginSucceed(self):
        return 'id' in [cookie.name for cookie in self.cookiejar]

    class ImdbFoundMovie:
        class Result:
            MATCH = 'match'
            NO_MATCH = 'no_match'
            BAD_MATCH = 'bad_match'
            FORCED_MATCH = 'forced_match'

        def __init__(self, code=None, title=None, year=None, title_ratio=None, result=Result.MATCH, url=None,
                     year_diff=None):
            if result != self.Result.MATCH and result != self.Result.FORCED_MATCH:
                if code is not None:
                    assert isinstance(url, str) and url.startswith('http')
                    pass
                assert code is None
                assert title is None
                assert year is None
                if result == self.Result.BAD_MATCH:
                    assert title_ratio == None
            self.__code = code
            self.__title = title
            self.__year = year
            self.__title_ratio = title_ratio
            self.__result = result
            self.__url = url
            self.__year_diff = year_diff
            pass

        def get_result(self):
            return self.__result

        def get_code(self):
            return self.__code

        def get_code_decoded(self):
            return self.__code.decode()

        def get_title(self):
            return self.__title

        def get_year(self):
            return self.__year

        def get_title_ratio(self):
            return self.__title_ratio

        def is_no_match(self):
            return self.__result == self.Result.NO_MATCH

        def is_bad_match(self):
            return self.__result == self.Result.BAD_MATCH

        def get_url(self):
            return self.__url

        def get_year_diff(self):
            return self.__year_diff

    def getMovieCode(self, mTitle, mYear):

        findList = []

        sUrlAdd = urllib.urlencode({'q': mTitle.encode('utf-8'), 's': 'all'})
        urlAdr = self.IMDBakas + "find?" + sUrlAdd

        intento = 0
        while intento < MAX_RETRY:
            try:
                webResponse = self.webSession.open(urlAdr)
                intento = 99
            except:
                intento = intento + 1
        if intento == MAX_RETRY:
            print("ERROR FOUND: Connection failed at imdb.getMovieCode() - " + mTitle + "(" + mYear + ")")
            return self.ImdbFoundMovie(result=self.ImdbFoundMovie.Result.BAD_MATCH)

        urlAdrRed = webResponse.geturl()
        urlHTML = webResponse.read()
        urlHTML = unicode(urlHTML, 'utf-8')

        if urlAdrRed.find("/title/tt") != -1:

            mCode = urlAdrRed[urlAdrRed.find("/title/tt") + len("/title/tt") - 2:urlAdrRed.find("/title/tt") + len(
                "/title/tt") + 7]
            pattern = re.compile(
                'itemprop="name">([\W\w]*?)<\/span>[\n\w\W]*?<span class="nobr">[\n\w\W]*?\(<a href="[\w\W]+?>(\d+)<\/a>')

            match = pattern.search(urlHTML)
            try:
                movieTitle = match.group(1)
                movieTitle = movieTitle.replace("\n", "")
            except:
                movieTitle = "Not Found"
            try:
                movieYear = match.group(2)
                movieYear = movieYear.replace("\n", "")
            except:
                movieYear = "0"

            return self.ImdbFoundMovie(mCode, movieTitle, movieYear)

        else:

            pattern = re.compile('"result_text"> <a href="\/title\/(tt\d+).*?>(.+?)<\/a>.*?\((\d+)\)',
                                 re.MULTILINE | re.DOTALL)
            iterator = pattern.finditer(urlHTML)

            for result in iterator:

                movieCode = str(result.group(1))
                movieYear = result.group(3)

                movieTitle = result.group(2)
                badCapture = movieTitle.find(';">')
                while badCapture != -1:
                    movieTitle = movieTitle[badCapture + 3:]
                    badCapture = movieTitle.find(';">')

                titleRatio = sDiff(None, mTitle, movieTitle).ratio()
                findList.append(
                    self.ImdbFoundMovie(code=movieCode, title=movieTitle, year=movieYear, title_ratio=titleRatio))

            # Find AKAS tittles.
            pattern = re.compile('"result_text"> <a href="\/title\/(tt\d+).*?\((\d+)\).*?aka.*?"(.*?)"',
                                 re.MULTILINE | re.DOTALL)
            akasIterator = pattern.finditer(urlHTML)

            for akaResult in akasIterator:
                akaTitle = akaResult.group(3)

                akaYear = akaResult.group(2)
                akaMovieCode = akaResult.group(1)

                titleRatio = sDiff(None, mTitle, akaTitle).ratio()

                if akaTitle.find(mTitle) != -1:
                    titleRatio2 = 0.6
                else:
                    titleRatio2 = 0

                titleRatio = max(titleRatio, titleRatio2)
                findList.append(
                    self.ImdbFoundMovie(code=akaMovieCode, title=akaTitle, year=akaYear, title_ratio=titleRatio))

            # Get the best match
            bestResult = self.ImdbFoundMovie(title_ratio=0, result=self.ImdbFoundMovie.Result.NO_MATCH)

            for movie in findList:
                if abs(int(movie.get_year()) - int(mYear)) <= 1:
                    if bestResult.get_title_ratio() < movie.get_title_ratio():
                        bestResult = movie

            if bestResult.get_title_ratio() > 0.5:
                return bestResult
            else:
                return self.ImdbFoundMovie(result=self.ImdbFoundMovie.Result.BAD_MATCH)

    def __found_movie_from_movie_dom_element(self, movie, mTitle, mYear):
        assert isinstance(movie, minidom.Element)
        description = movie.getElementsByTagName("Description")
        for a in description:
            if (a.childNodes[0].nodeValue[:4]).isnumeric:
                # Some times isnumeric is not working ¿unicode type problem?
                sYear = a.childNodes[0].nodeValue[:4]
                sYear = filter(type(sYear).isdigit, sYear)
                sYear = "0" + sYear
                year = int(sYear)

        movieFoundTitle = movie.childNodes[0].nodeValue
        movieFoundYear = year
        movieFoundCode = movie.getAttribute("id")

        titleRatio = sDiff(None, mTitle, movieFoundTitle).ratio()
        year_diff = int(movieFoundYear) - int(mYear)

        # print("API: " + str(movieFoundTitle) + " | " + str(movieFoundYear) + " | " + str(movieFoundCode) + " | Ratio: " + str(titleRatio))
        found_movie = self.ImdbFoundMovie(code=movieFoundCode, title=movieFoundTitle, year=movieFoundYear,
                                          title_ratio=titleRatio, url=self.getMovieUrl(movieFoundCode),
                                          year_diff=year_diff)
        return found_movie

    def __get_best_match_from_2(self, left, right):
        pass

    def __get_best_match(self, found_movies, mYear):
        # Get the best match
        bestResult = self.ImdbFoundMovie(title_ratio=0, result=self.ImdbFoundMovie.Result.NO_MATCH)
        for movie in found_movies:
            assert isinstance(movie, self.ImdbFoundMovie)
            a = self.__get_best_match_from_2(bestResult, movie)
            if abs(movie.get_year_diff()) <= 1:
                if bestResult.get_title_ratio() < movie.get_title_ratio():
                    bestResult = movie

        if bestResult.get_title_ratio() > 0.5:
            return bestResult
        else:
            # This is a very optimistic way of think, but for my movie list it works nice.
            if len(found_movies) > 0:
                if str(found_movies[0].get_year()) == mYear:
                    return found_movies[0]
                else:
                    # No result.
                    return self.ImdbFoundMovie(result=self.ImdbFoundMovie.Result.BAD_MATCH)
            else:
                # No result.
                return self.ImdbFoundMovie(result=self.ImdbFoundMovie.Result.BAD_MATCH)

    def getMovieCodeByAPI(self, mTitle, mYear):
        found_movies = []

        sUrlAdd = urllib.urlencode({'q': mTitle.encode('utf-8')})
        urlAdr = self.IMDBbyTitleAPI + sUrlAdd

        intento = 0
        webResponse = None
        while webResponse is None:
            try:
                webResponse = self.webSession.open(urlAdr)
            except:
                intento += 1
                if intento >= MAX_RETRY:
                    print("ERROR FOUND: Connection failed at imdb.getMovieCodeByAPI() - " + mTitle + " (" + mYear + ")")
                    return self.ImdbFoundMovie(result=self.ImdbFoundMovie.Result.BAD_MATCH)

        urlHTML = webResponse.read()
        # urlHTML = unicode(urlHTML, 'utf-8')

        IMDBfoundAPI = minidom.parseString(urlHTML)
        movies_dom_elements = IMDBfoundAPI.getElementsByTagName("ImdbEntity")

        for movie_dom_element in movies_dom_elements:
            found_movie = self.__found_movie_from_movie_dom_element(movie_dom_element, mTitle, mYear)
            assert isinstance(found_movie, self.ImdbFoundMovie)
            found_movies.append(found_movie)

        return self.__get_best_match(found_movies, mYear)

    def voteMovie(self, mCode, mVote):
        urlAdr = "http://www.imdb.com/title/" + mCode + "/vote"
        webResponse = self.webSession.open(urlAdr)

        html = webResponse.read()

        # OLD CODE:
        # pattern = re.compile (mCode + '\/vote\?v='+ str(mVote) +'&k=(.*?)"')  
        # iterator = pattern.finditer(html)

        # for element in iterator:
        #     voteHash = element.group(1)
        # urlAdr = self.IMDBakas + "title/" + mCode + "/vote?v=" + str(mVote) + "&k=" + voteHash

        pattern = re.compile('<input type="hidden" name="k" value="([\w\W]+?)">')
        matches = pattern.findall(html)

        try:
            urlAdr = "http://www.imdb.com/title/" + mCode + "/vote?k=" + matches[0] + "&v=" + str(
                mVote) + "&cast.x=11&cast.y=6&cast=Cast+vote"
            webResponse = self.webSession.open(urlAdr)

            return 1
        except:
            return -1

    def getMovieUrl(self, code):
        assert isinstance(code, (unicode, str))
        assert len(code) == 9
        assert code.startswith('tt')
        return 'http://www.imdb.com/title/{}/'.format(code)

    def get_from_code(self, code):
        url = 'http://www.omdbapi.com/?i={}&plot=full&r=json'.format(code)
        webResponse = self.webSession.open(url)

        html = webResponse.read()
        import json
        jojo = json.loads(html)
        res = self.ImdbFoundMovie(code=code, title=jojo['Title'], year=jojo['Year'],
                                  result=self.ImdbFoundMovie.Result.FORCED_MATCH,
                                  url=self.getMovieUrl(code))
        return res

    def match_alg_2(self, title, year):
        imdb = self
        imdbID = imdb.getMovieCodeByAPI(title, year)
        if imdbID.is_bad_match():
            imdbID = imdb.getMovieCode(title, year)
        if imdbID.is_bad_match():
            t = re.sub('\([\w\W]*?\)', '', title).strip()
            imdbID = imdb.getMovieCode(t, year)
        return imdbID
