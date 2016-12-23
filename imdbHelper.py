# -*- coding: utf-8 -*-

import sys
import re
#import cookielib, urllib, urllib2
import requests
from difflib import SequenceMatcher as sDiff
from xml.dom import minidom
from bs4 import BeautifulSoup

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

WORKERS = 4  # Mutli-Thread workers
MAX_RETRY = 10


class IMDBhelper:
    """Clase para ayudar a bajar la informacion de imdb"""

    # IMDB URL set.
    IMDBurlLogin = "https://secure.imdb.com/register-imdb/login#"
    IMDBvotedPrefix = "http://www.imdb.com/user/ur5741926/ratings?start="
    IMDBvotedSufix = "&view=detail&sort=title:asc&defaults=1&my_ratings=restrict&scb=0.28277816087938845"
    IMDBakas = "http://akas.imdb.com/"
    IMDBbyTitleAPI = "http://www.imdb.com/xml/find?"
    IMDBurlCaptcha = "https://secure.imdb.com/widget/captcha?type="

    cookiejar = None
    webSession = None

    def __init__(self):
        self.userName = ""
        self.userPass = ""
        self.userId = ""

        # Enable cookie support for urllib2
        #self.cookiejar = cookielib.CookieJar() # DELETE
        #self.webSession = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar)) # DELETE
        self.webSession = requests.Session()
        
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
                webResponse = self.webSession.get(self.IMDBurlLogin)
                intento = MAX_RETRY
            except:
                intento = intento + 1
        if intento == MAX_RETRY:
            print("ERROR FOUND: Connection failed at imdbHelper.login()")
        else:
            
            pattern = re.compile('<a href="(https:\/\/www.imdb.com\/ap\/signin\?[\w\W]+?)"')
            html = webResponse.text
            ulr_imdb_login = pattern.search(html).group(1)
            
            driver = webdriver.Chrome()
            driver.get(ulr_imdb_login);
            time.sleep(5)
            search_box = driver.find_element_by_name('email')
            search_box.send_keys(self.userName)
            search_box = driver.find_element_by_name('password')
            search_box.send_keys(self.userPass)
            search_box.submit()
            time.sleep(5)
            cookies = driver.get_cookies()
            s = requests.Session()
            for cookie in cookies:
                self.webSession.cookies.set(cookie['name'], cookie['value'])
            driver.quit()
            
            if not 'id' in [cookie.name for cookie in self.webSession.cookies]:
                print("Login error!: Incorrect IMDB User or password, please try again.")

    # returns 1 when login is succeed
    def loginSucceed(self):
        return 'id' in [cookie.name for cookie in self.webSession.cookies]

    def getMovieCode(self, mTitle, mYear):

        findList = []
        
        intento = 0
        while intento < MAX_RETRY:
            try:
                webResponse = self.webSession.get(self.IMDBakas + 'find', params={'ref_': 'nv_sr_fn', 'q': mTitle.encode('utf-8'), 's':'all' })
                intento = 99
            except:
                intento = intento + 1
        if intento == MAX_RETRY:
            print("ERROR FOUND: Connection failed at imdb.getMovieCode() - " + mTitle + "(" + mYear + ")")
            return self.ImdbFoundMovie(result=self.ImdbFoundMovie.RESULT_BAD_MATCH)
        
        urlAdrRed = webResponse.url
        urlHTML = webResponse.text
        
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
                findList.append(self.ImdbFoundMovie(code=movieCode, title=movieTitle, year=movieYear, ratio=titleRatio))

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
                findList.append(self.ImdbFoundMovie(code=akaMovieCode, title=akaTitle, year=akaYear, ratio=titleRatio))

            # Get the best match
            bestResult = self.ImdbFoundMovie(ratio=0, result=self.ImdbFoundMovie.RESULT_NO_MATCH)

            for movie in findList:
                if abs(int(movie.get_year()) - int(mYear)) <= 1:
                    if bestResult.get_ratio() < movie.get_ratio():
                        bestResult = movie

            if bestResult.get_ratio() > 0.5:
                return bestResult
            else:
                return self.ImdbFoundMovie(result=self.ImdbFoundMovie.RESULT_BAD_MATCH)

    class ImdbFoundMovie:
        RESULT_MATCH = 'match'
        RESULT_NO_MATCH = 'no_match'
        RESULT_BAD_MATCH = 'bad_match'

        def __init__(self, code=None, title=None, year=None, ratio=None, result=RESULT_MATCH):
            if result != self.RESULT_MATCH:
                if code is not None:
                    pass
                assert code is None
                assert title is None
                assert year is None
                if result == self.RESULT_BAD_MATCH:
                    assert ratio == None
            self.__code = code
            self.__title = title
            self.__year = year
            self.__ratio = ratio
            self.__result = result
            pass
        def __repr__(self):
            s = u"<ImdbFoundMovie Title: {0}, Year: {1}, Ratio: {2} Result: {3}, Code: {4}>".format(self.__title, self.__year, self.__ratio, self.__result, self.__code)
            return s.encode('ascii', 'backslashreplace')
        
        def __str__(self):
            s = u"Title: {0}, Year: {1}, Ratio: {2} Result: {3}, Code: {4}".format(self.__title, self.__year, self.__ratio, self.__result, self.__code)
            return s.encode('ascii', 'backslashreplace')
        
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

        def get_ratio(self):
            return self.__ratio

        def is_no_match(self):
            return self.__result == self.RESULT_NO_MATCH

        def is_bad_match(self):
            return self.__result == self.RESULT_BAD_MATCH

    def getMovieCodeByAPI(self, mTitle, mYear):

        findList = []
        intento = 0
        while intento < MAX_RETRY:
            try:
                webResponse = self.webSession.get(self.IMDBbyTitleAPI, params={'q': mTitle.encode('utf-8')})
                intento = 99
            except:
                intento = intento + 1
        if intento == MAX_RETRY:
            print("ERROR FOUND: Connection failed at imdb.getMovieCodeByAPI() - " + mTitle + " (" + mYear + ")")
            return self.ImdbFoundMovie(result=self.ImdbFoundMovie.RESULT_BAD_MATCH)

        # urlHTML = webResponse.text
        
        # Let's some magic to happen
        soup = BeautifulSoup(webResponse.text) 
        urlHTML = soup.get_text()
        # Magic is done
        # I will be very glad if someone explain me why does it work
        
        IMDBfoundAPI = minidom.parseString(urlHTML)
        movies = IMDBfoundAPI.getElementsByTagName("ImdbEntity")
        
        for movie in movies:
            description = movie.getElementsByTagName("Description")
            for a in description:
                
                rc = []
                for node in a:
                    if node.nodeType == node.TEXT_NODE:
                        rc.append(node.data)
                print ''.join(rc)
                
                
                
                
                
                
                
                
                
                
                
                
                
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

            # print("API: " + str(movieFoundTitle) + " | " + str(movieFoundYear) + " | " + str(movieFoundCode) + " | Ratio: " + str(titleRatio))
            findList.append(self.ImdbFoundMovie(code=movieFoundCode, title=movieFoundTitle, year=movieFoundYear,
                                                ratio=titleRatio))

        # Get the best match
        bestResult = self.ImdbFoundMovie(ratio=0, result=self.ImdbFoundMovie.RESULT_NO_MATCH)
        for movie in findList:
            if abs(int(movie.get_year()) - int(mYear)) <= 1:
                if bestResult.get_ratio() < movie.get_ratio():
                    bestResult = movie

        if bestResult.get_ratio() > 0.5:
            return bestResult

        else:
            # This is a very optimistic way of think, but for my movie list it works nice.
            if len(findList) > 0:
                if str(findList[0].get_year()) == mYear:
                    return findList[0]
                else:
                    # No result.
                    return self.ImdbFoundMovie(result=self.ImdbFoundMovie.RESULT_BAD_MATCH)
            else:
                # No result.
                return self.ImdbFoundMovie(result=self.ImdbFoundMovie.RESULT_BAD_MATCH)

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
