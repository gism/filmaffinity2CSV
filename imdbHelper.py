# -*- coding: utf-8 -*-

import re
import sys
from difflib import SequenceMatcher as sDiff
from xml.dom import minidom

import cookielib
import urllib
import urllib2


class IMDBhelper:
    """Clase para ayudar a bajar la informacion de imdb"""

    # IMDB URL set.

    MAX_RETRY = 10
    Imdbcom = 'imdb.com'
    IMDBurlLogin = "https://secure.{}/register-imdb/login#".format(Imdbcom)
    IMDBvotedPrefix = "http://www.{}/user/ur5741926/ratings?start=".format(Imdbcom)
    IMDBvotedSufix = "&view=detail&sort=title:asc&defaults=1&my_ratings=restrict&scb=0.28277816087938845"
    IMDBbyTitleAPI = "http://www.{}/xml/find?xml=1&nr=1&tt=on&".format(Imdbcom)
    IMDBurlCaptcha = "https://secure.{}/widget/captcha?type=".format(Imdbcom)

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

        webResponse = self.__webSession_open_retry(self.IMDBurlLogin, '')
        if webResponse is None:
            print("ERROR FOUND: Connection failed at imdbHelper.login()")
            return

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
            raise Exception("Login error!: Incorrect IMDB User or password, please try again.")

    # returns 1 when login is succeed
    def loginSucceed(self):
        return 'id' in [cookie.name for cookie in self.cookiejar]

    class ImdbFoundMovie:
        class Result:
            MATCH = 'match'
            NO_MATCH = 'no_match'
            BAD_MATCH = 'bad_match'
            FORCED_MATCH = 'forced_match'

        def __init__(self, code=None, title=None, year=None, search_title=None, result=Result.MATCH,
                     search_year=None):

            try:
                assert search_title is not None and isinstance(search_title, unicode) and len(search_title) > 0
            except:
                raise
            assert search_year is not None and isinstance(search_year, unicode) and len(search_year) > 0

            if result == self.Result.NO_MATCH or result == self.Result.BAD_MATCH:
                assert code is None
                assert title is None
                assert year is None
            elif result == self.Result.MATCH or result == self.Result.FORCED_MATCH:
                assert code is not None
                if code.startswith('tt'):
                    code = code[2:]
                assert len(code) == 7
                assert title is not None and isinstance(title, unicode) and len(title) > 0

                try:
                    assert year is not None
                    if isinstance(year, (str, unicode)):
                        year = int(year)
                    assert isinstance(year, int)
                except:
                    raise
            else:
                raise NotImplementedError()
            self.__code = code
            self.__title = title
            self.__year = year
            self.__search_title = search_title
            self.__result = result
            self.__search_year = search_year
            pass

        def get_result(self):
            return self.__result

        def get_code(self):
            return 'tt' + self.__code

        def get_code_decoded(self):
            return self.get_code().decode()

        def get_title(self):
            return self.__title

        def get_year(self):
            return self.__year

        def get_title_ratio(self):
            try:
                titleRatio = sDiff(None, self.__search_title, self.__title).ratio()
            except:
                raise
            return titleRatio

        def is_no_match(self):
            return self.__result == self.Result.NO_MATCH

        def is_bad_match(self):
            return self.__result == self.Result.BAD_MATCH

        def get_url(self):
            return self.getMovieUrl()

        def get_year_diff(self):
            try:
                year_diff = int(self.__year) - int(self.__search_year)
            except:
                raise
            return year_diff

        def could_match(self):
            if self.bad_or_no_match():
                return False
            if self.get_year_diff() > 1:
                return False
            if self.get_title_ratio() <= 0.5:
                return False
            return True

        def bad_or_no_match(self):
            left = self
            return left.is_bad_match() or left.is_no_match()

        def get_best_match_from_2(self, right):
            assert isinstance(right, self.__class__)
            left = self

            if left.bad_or_no_match() and not right.bad_or_no_match():
                return right
            elif not left.bad_or_no_match() and right.bad_or_no_match():
                return left

            if left.could_match() and not right.could_match():
                return left
            elif not left.could_match() and right.could_match():
                return right

            if left.get_title_ratio() < right.get_title_ratio():
                return right
            else:
                return left

        def getMovieUrl(self):
            assert self.__result == self.Result.MATCH or self.__result == self.Result.FORCED_MATCH
            code = self.get_code()
            assert isinstance(code, (unicode, str))
            assert len(code) == 9
            assert code.startswith('tt')
            url = 'http://www.imdb.com/title/{}/'.format(code)

            assert url is not None and isinstance(url, str) and url.startswith('http')
            return url

    def __webSession_open_retry(self, urlAdr, sufix):
        intento = 0
        webResponse = None
        while webResponse is None:
            try:
                webResponse = self.webSession.open(urlAdr)
            except:
                intento += 1
                if intento >= self.MAX_RETRY:
                    print("ERROR FOUND: Connection failed at imdb.__webSession_open_retry() - " + sufix)
                    return

        return webResponse

    def movie_find_via_akas(self, mTitle, mYear):
        IMDBakas = "http://akas.{}/".format(self.Imdbcom)
        findList = []

        sUrlAdd = urllib.urlencode({'q': mTitle.encode('utf-8'), 's': 'all'})
        urlAdr = IMDBakas + "find?" + sUrlAdd

        webResponse = self.__webSession_open_retry(urlAdr, mTitle + "(" + mYear + ")")
        if webResponse is None:
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

            return self.ImdbFoundMovie(code=mCode, title=movieTitle, year=movieYear)

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

                findList.append(
                    self.ImdbFoundMovie(code=movieCode, title=movieTitle, year=movieYear, search_title=mTitle,
                                        search_year=mYear))

            # Find AKAS tittles.
            pattern = re.compile('"result_text"> <a href="\/title\/(tt\d+).*?\((\d+)\).*?aka.*?"(.*?)"',
                                 re.MULTILINE | re.DOTALL)
            akasIterator = pattern.finditer(urlHTML)

            for akaResult in akasIterator:
                akaTitle = akaResult.group(3)

                akaYear = akaResult.group(2)
                akaMovieCode = akaResult.group(1)

                findList.append(
                    self.ImdbFoundMovie(code=akaMovieCode, title=akaTitle, year=akaYear, search_title=mTitle,
                                        search_year=mYear))

            # Get the best match
            bestResult = self.__get_best_match(findList, mTitle, mYear)

            if bestResult.could_match():
                return bestResult
            else:
                return self.ImdbFoundMovie(result=self.ImdbFoundMovie.Result.BAD_MATCH, search_title=mTitle,
                                           search_year=mYear)

    def __found_movie_from_movie_dom_element(self, movie, mTitle, mYear):
        assert isinstance(movie, minidom.Element)
        description = movie.getElementsByTagName("Description")
        assert len(description) == 1
        for a in description:
            juju = a.childNodes[0].nodeValue[:4]
            if True or juju.isnumeric():
                # Some times isnumeric is not working ¿unicode type problem?
                sYear = juju
                sYear = filter(type(sYear).isdigit, sYear)
                sYear = "0" + sYear
                year = int(sYear)

        movieFoundTitle = movie.childNodes[0].nodeValue
        movieFoundYear = year
        movieFoundCode = movie.getAttribute("id")

        found_movie = self.ImdbFoundMovie(code=movieFoundCode, title=movieFoundTitle, year=movieFoundYear,
                                          search_title=mTitle,
                                          search_year=mYear)
        return found_movie

    def __get_best_match(self, found_movies, mTitle, mYear):
        # Get the best match
        bestResult = self.ImdbFoundMovie(result=self.ImdbFoundMovie.Result.NO_MATCH, search_year=mYear,
                                         search_title=mTitle)
        for movie in found_movies:
            assert isinstance(movie, self.ImdbFoundMovie)
            if movie.get_code() == "tt0970416":
                pass
            bestResult = bestResult.get_best_match_from_2(movie)

        if bestResult.could_match():
            return bestResult

        # This is a very optimistic way of think, but for my movie list it works nice.
        if len(found_movies) > 0:
            if str(found_movies[0].get_year()) == mYear:
                return found_movies[0]

        # No result.
        return self.ImdbFoundMovie(result=self.ImdbFoundMovie.Result.BAD_MATCH, search_year=mYear, search_title=mTitle)

    def movie_find_via_api(self, mTitle, mYear):
        found_movies = []

        sUrlAdd = urllib.urlencode({'q': mTitle.encode('utf-8')})
        urlAdr = self.IMDBbyTitleAPI + sUrlAdd

        webResponse = self.__webSession_open_retry(urlAdr, mTitle + " (" + mYear + ")")
        if webResponse is None:
            return self.ImdbFoundMovie(result=self.ImdbFoundMovie.Result.BAD_MATCH)

        urlHTML = webResponse.read()
        # urlHTML = unicode(urlHTML, 'utf-8')

        IMDBfoundAPI = minidom.parseString(urlHTML)
        movies_dom_elements = IMDBfoundAPI.getElementsByTagName("ImdbEntity")

        for movie_dom_element in movies_dom_elements:
            found_movie = self.__found_movie_from_movie_dom_element(movie_dom_element, mTitle, mYear)
            assert isinstance(found_movie, self.ImdbFoundMovie)
            found_movies.append(found_movie)

        return self.__get_best_match(found_movies, mTitle, mYear)

    def movie_vote(self, mCode, mVote):
        urlAdr = "http://www.imdb.com/title/" + mCode + "/vote"
        webResponse = self.webSession.open(urlAdr)

        html = webResponse.read()

        pattern = re.compile('<input type="hidden" name="k" value="([\w\W]+?)">')
        matches = pattern.findall(html)

        try:
            urlAdr = "http://www.imdb.com/title/" + mCode + "/vote?k=" + matches[0] + "&v=" + str(
                mVote) + "&cast.x=11&cast.y=6&cast=Cast+vote"
            webResponse = self.webSession.open(urlAdr)

            return 1
        except:
            return -1

    def movie_get_from_code_via_api(self, code, title, year):
        url = 'http://www.omdbapi.com/?i={}&plot=full&r=json'.format(code)
        webResponse = self.webSession.open(url)

        html = webResponse.read()
        import json
        json_response = json.loads(html)
        try:
            res = self.ImdbFoundMovie(code=code, title=json_response['Title'], year=int(json_response['Year']),
                                      result=self.ImdbFoundMovie.Result.FORCED_MATCH, search_title=title,
                                      search_year=year)
        except:
            raise
        return res

    def movie_find_via_imdblib(self, stitle, syear):
        if stitle == u'Spanish Affair 2':
            pass
        from imdb import IMDb
        ia = IMDb()
        try:
            movies = ia.search_movie(stitle)
        except:
            return
        for movie in movies:
            kind = movie['kind']
            if not kind == u'movie':
                pass
            if kind == u'video game':
                continue
            assert kind == u'movie' or kind == u'tv series' or kind == u'episode' or kind == u'tv mini series'
            title = movie['title']
            year = movie['year']
            movie_id = movie.movieID
            pass
            found_movie = self.ImdbFoundMovie(code=movie_id, title=title, year=year, search_title=stitle,
                                              result=self.ImdbFoundMovie.Result.MATCH, search_year=syear)
            if abs(found_movie.get_year_diff()) <= 1:
                return found_movie
            pass
        if not stitle == u'Spanish Affair 2':
            pass
        pass

    class ImdbVote:
        def __init__(self, code, title, year, yourrate, allrate, number, episode_title):
            self.code = code
            self.title = title
            self.year = year
            self.rate = yourrate
            self.allrate = allrate
            self.number = number
            """ Index in vote html pages"""
            self.episode_title = episode_title
            pass

    def __vote_parse_numpages(self, soupPage):
        pagination = soupPage.body.findAll('div', attrs={'class': 'pagination'})

        assert len(pagination) == 1
        pass
        blu = pagination[0].text
        blo = blu.split('\n')
        blo2 = blo[2].split()
        assert blo2[0] == 'Page'
        assert blo2[2] == 'of'
        currentpage = int(blo2[1])
        numpages = int(blo2[3])
        return numpages

    def __vote_parse_movieDiv(self, movieDiv):
        tit = movieDiv.b.a.text
        year = movieDiv.b.span.text
        year_string = year.split()[0].replace('(', '').replace(')', '').replace(' ', '')
        year_int = int(year_string)
        number_element = movieDiv.previous_sibling.previous_sibling
        assert number_element['class'] == ['number']
        number = int(number_element.text.replace('.', ''))
        episodes = movieDiv.findAll('div', class_="episode", recursive=False)
        if len(episodes) > 0:
            assert len(episodes) == 1
            episode_title = episodes[0].a.text
            pass
        else:
            episode_title = None
        id2s = movieDiv.findAll('div', class_="rating rating-list", recursive=False)

        assert len(id2s) == 1
        id2s2 = id2s[0]
        id2 = id2s2['id']
        code, temp, yourrate, allrate, temp2 = id2.split('|')
        pass
        return self.ImdbVote(code=code, title=tit, year=year_int, yourrate=yourrate, allrate=allrate, number=number,
                             episode_title=episode_title)

    def __vote_parse_votecount(self, soupPage):

        if True:
            spans = soupPage.body.findAll('span')
            votecounterspan = None
            for span1 in spans:
                tt = span1.text
                if 'Titles' in tt:
                    assert votecounterspan is None
                    votecounterspan = span1
                pass
            assert votecounterspan is not None
        else:
            # this does not work
            pagination = soupPage.body.findAll('div', attrs={'class': 'desc'})
            aa = len(pagination)
            assert aa == 1
            votecounterspan = pagination[0].span
        bb = votecounterspan.text
        cc = bb.split()
        dd = cc[0].replace('(', '')
        return int(dd)
        pass

    def __vote_page(self, url):
        webResponse = self.webSession.open(url)

        html = webResponse.read()  # .strip()
        if False:
            # This fails! does not correctly validate html
            IMDBfoundAPI = minidom.parseString(html)
            movies_dom_elements = IMDBfoundAPI.getElementsByTagName("ImdbEntity")
        else:
            from bs4 import BeautifulSoup
            soupPage = BeautifulSoup(html, 'html.parser')
            vote_count = self.__vote_parse_votecount(soupPage)
            numpages = self.__vote_parse_numpages(soupPage)
            daysDiv = soupPage.body.findAll('div', attrs={'class': 'info'})
            for movieDiv in daysDiv:
                vote = self.__vote_parse_movieDiv(movieDiv)
                assert isinstance(vote, self.ImdbVote)
                yield vote_count, numpages, vote
                pass
            pass

    def votes(self):
        url = 'http://www.imdb.com/user/ur57660764/ratings?ref_=nv_usr_rt_4'
        numpages = None
        vote_counter = 0
        for vote_count, numpages, vote in self.__vote_page(url):
            vote_counter += 1
            yield vote
        for current_page in range(2, numpages + 1):
            url2 = 'http://www.imdb.com/user/ur57660764/ratings?start=101&view=detail&sort=ratings_date:desc'
            url2 = 'http://www.imdb.com/user/ur57660764/ratings?start={}&view=detail&sort=ratings_date:desc'.format(
                (current_page - 1) * 100 + 1)
            for vote_count2, numpages2, vote in self.__vote_page(url2):
                assert numpages2 == numpages
                assert vote_count2 == vote_count
                vote_counter += 1
                yield vote
        pass
        assert vote_count == vote_counter

    pass
