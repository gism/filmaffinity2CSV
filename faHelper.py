# -*- coding: utf-8 -*-

import threading, Queue
import sys
import re
import cookielib, urllib, urllib2
from bs4 import BeautifulSoup


WORKERS = 4  # Mutli-Thread workers


# From October 12, 2015 to 20151012
def changeDateString(dateBad):
    date = dateBad.split(" ")
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

    dateGood = date[2] + date[0] + date[1]
    return dateGood


class FAhelper:
    """Clase para ayudar a bajar la informacion de filmaffinity"""

    # FA URL set.
    # urlLogin= "http://www.filmaffinity.com/en/login.php"
    urlLogin = "https://filmaffinity.com/en/account.ajax.php?action=login"  # New login URL? seems it works
    urlVotes = "http://www.filmaffinity.com/en/myvotes.php"
    urlVotes_prefix = "http://www.filmaffinity.com/en/myvotes.php?p="
    urlVotes_sufix = "&orderby="
    urlVotesID = "https://www.filmaffinity.com/en/userratings.php?user_id="
    urlVotesIDpageSufix = "&p="

    urlFilm = "http://www.filmaffinity.com/en/film"
    urlFilmSufix = ".html"

    urlMain = "http://www.filmaffinity.com/en/main.php"

    cookiejar = None
    webSession = None

    faMovies = []
    faMoviesFilled = []

    def __init__(self):
        self.userName = ""
        self.userPass = ""
        self.userId = "0"

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

    # returns value of film affinity user ID
    def getUserID(self):
        return self.userId

    def login(self):
        user, password = self.getUser()

        self.webSession.open(self.urlLogin)

        # Post data to Filmaffinity login URL.
        dataForm = {"postback": 1, "rp": "", "username": user,
                    "password": password}
        dataPost = urllib.urlencode(dataForm)
        request = urllib2.Request(self.urlLogin, dataPost)
        self.webSession.open(request)  # Our cookiejar automatically receives the cookies, after the request

        webResponse = self.webSession.open(self.urlVotes)
        pattern = re.compile('\?user_id=(\d+)"')
        match = pattern.search(webResponse.read())

        if match:
            userID = match.group(1)
        else:
            print(
                "ERROR FOUND: change regular expression at login() for user ID. Probably FA changed web page structure")
            sys.exit("Error happens, check log.")

        self.userId = userID

    # returns 1 when login is succeed
    def loginSucceed(self):
        return len(self.cookiejar) > 1
    
    def getNumVotes(self):

        if self.userId == "0":
            print("ERROR FOUND: No user id found. Please login or set user id.")
            sys.exit("Error happens, check log.")
            return

        url = self.urlVotesID + self.userId
        webResponse = self.webSession.open(url)
        html = webResponse.read()
        
        numPages = 0
        soupPage = BeautifulSoup(html, 'html.parser')
        pagesDiv = soupPage.body.findAll('div', attrs={'class': 'pager'})
        for page in pagesDiv:
            for link in page.findAll('a'):
                if (link.string.isnumeric()):
                    if(int(link.string) > int(numPages)):
                        numPages = int(link.string)
        
        numVotes = 0
        for div in soupPage.body.findAll('div', attrs={'class': 'number'}):
            i = div.findAll('i', attrs={'class': 'fa fa-film'})
            if i != []:
                if(div.text.replace(",","").isnumeric()):
                    numVotes = int(div.text.replace(",",""))       
  
        return numVotes, numPages

    class FAMovieData:

        def __init__(self, movieID, movieTitle, movieYear, movieRate, dayYYYYMMDD):
            self.movieID = movieID
            self.movieTitle = movieTitle
            self.movieYear = movieYear
            self.movieRate = movieRate
            self.dayYYYYMMDD = dayYYYYMMDD
                        
            self.movieFaRate = None
            self.movieFaVotes = None
            self.movieCountry = None
            self.movieDirector = None
            self.movieCast = None
            self.movieGenre = None
            self.movieDuration = None
            self.movieSynopsis = None
            
        def set_movie_details(self, movieFaRate, movieFaVotes, movieCountry, movieDirector, movieCast, movieGenre, movieDuration, movieSynopsis):
            self.movieFaRate = movieFaRate
            self.movieFaVotes = movieFaVotes
            self.movieCountry = movieCountry
            self.movieDirector = movieDirector
            self.movieCast = movieCast
            self.movieGenre = movieGenre
            self.movieDuration = movieDuration
            self.movieSynopsis = movieSynopsis
            
        def get_id(self):
            return self.movieID

        def get_title(self):
            return self.movieTitle

        def get_year(self):
            return self.movieYear

        def get_rate(self):
            return self.movieRate

        def get_rate_dayYYYYMMDD(self):
            return self.dayYYYYMMDD

        def get_FA_rate(self):
            return self.movieFaRate
        
        def get_FA_votes(self):
            return self.movieFaVotes
        
        def get_country(self):
            return self.movieCountry
        
        def get_director(self):
            return self.movieDirector
        
        def get_cast(self):
            return self.movieCast
        
        def get_genre(self):
            return self.movieGenre
            
        colum_names = ("ID", "Title", "Year", "Vote", "Voted", "FA rate", "FA votes", "Country", "Director", "Cast", "Genre", "Duration", "Synopsis")

        def tabulate1(self):
            return self.movieID, self.movieTitle, self.movieYear, self.movieRate, self.dayYYYYMMDD, self.movieFaRate, self.movieFaVotes, self.movieCountry, self.movieDirector, self.movieCast, self.movieGenre, self.movieDuration, self.movieSynopsis 
        
        def __repr__(self):
            s = u"<FAMovieData CLASS: Title: {0}, Year: {1}, ID: {2}, Rated: {3} on {4}, FA rate {5}, FA votes {6}, duraion: {7}, Country: {8} Director: {9}, Cast: {10}, Genre: {11}, Synopsis {12}>".format(
                self.movieTitle, self.movieYear, self.movieID, self.movieRate, self.dayYYYYMMDD, self.movieFaRate, self.movieDuration,
                self.movieCountry, self.movieDirector, self.movieCast, self.movieGenre, self.movieSynopsis)
            return s.encode('ascii', 'backslashreplace')
        
        def __str__(self):
            s = u"[Title: {0}, Year: {1}, ID: {2}, Rated: {3} on {4}, FA rate {5}, FA votes {6}, duration: {7}, Country: {8} Director: {9}, Cast: {10}, Genre: {11}, Synopsis {12}]".format(
                self.movieTitle, self.movieYear, self.movieID, self.movieRate, self.dayYYYYMMDD, self.movieFaRate, self.movieFaVotes, self.movieDuration,
                self.movieCountry, self.movieDirector, self.movieCast, self.movieGenre, self.movieSynopsis)
            return s.encode('ascii', 'backslashreplace')
        
    def getDumpVotesPage(self, page):

        if self.userId == "0":
            print("ERROR FOUND: No user id found. Please login or set user id.")
            sys.exit("Error happens, check log.")
            return

        url = self.urlVotesID + str(self.userId) + self.urlVotesIDpageSufix + str(page)
        webResponse = self.webSession.open(url)
        html = webResponse.read()
        html = unicode(html, 'utf-8')

        #Check if FA has blocked
        if "<title>Too many request</title>" in html:
            self.solveRobot(url)
            webResponse = self.webSession.open(url)

            html = webResponse.read()
            html = unicode(html, 'utf-8')
            
            if webResponse.getcode() != 200:
                intento = intento + 1
                    
        soupPage = BeautifulSoup(html, 'html.parser')
        daysDiv = soupPage.body.findAll('div', attrs={'class': 'user-ratings-wrapper'})
        
        for dayDiv in daysDiv:

            # Get day when the vote was done:
            day = dayDiv.find('div', attrs={'class': 'user-ratings-header'})
            dayBadFormat = day.text.replace("Rated on ", "")
            dayYYYYMMDD = changeDateString(dayBadFormat)

            # Each day may have more than one movie:
            rates = dayDiv.findAll('div', attrs={'class': 'user-ratings-movie fa-shadow'})
            for movie in rates:
                    
                # Get filmaffinity ID
                try:
                    movieID = movie.find('div', attrs={'class': 'movie-card movie-card-1'}).get("data-movie-id")
                except AttributeError:
                    movieID = "000000"
                
                # Get movie personal rate
                try:
                    movieRate = movie.find('div', attrs={'class': 'ur-mr-rat'}).text
                except AttributeError:
                    movieRate = -1
                
                # Get movie filmaffinity rate
                try:
                    movieFaRate = movie.find('div', attrs={'class': 'avgrat-box'}).text
                except AttributeError:
                    movieFaRate = -1
                
                # Get movie filmaffinity votes
                try:
                    movieFaVotes = movie.find('div', attrs={'class': 'ratcount-box'}).text
                except AttributeError:
                    movieFaVotes = -1
                
                # Get title div
                titleDiv = movie.find('div', attrs={'class': 'mc-title'})
                
                # But before, get movie country
                imgDiv = titleDiv.find('img', alt=True)
                movieCountry = imgDiv['alt']
                
                # Get title div
                pattern = re.compile('\((\d\d\d\d)\)')
                match = pattern.search(titleDiv.text)
                if match:
                    movieYear = match.group(1)
                    movieTitle = titleDiv.text.replace("(" + movieYear + ")", "").strip()
                    movieTitle = movieTitle.replace("(TV Series)", "").strip()
                    movieTitle = movieTitle.replace("(TV)", "").strip()
                    movieTitle = movieTitle.replace("(S)", "").strip()
                else:
                    print(
                        "ERROR FOUND: change regular expression at getDumpVotesPage() for movie year. Probably FA changed web page structure")
                    sys.exit("Error happens, check log.")
                    
                movieResult = self.FAMovieData(movieID=movieID, movieTitle=movieTitle, movieYear=movieYear,
                                               movieRate=movieRate, dayYYYYMMDD=dayYYYYMMDD)
                
                movieResult.set_movie_details(movieFaRate=movieFaRate, movieFaVotes=movieFaVotes, movieCountry=movieCountry, 
                                              movieDirector = None, movieCast = None, movieGenre = None, movieDuration = None, movieSynopsis = None)
                
                self.faMovies.append(movieResult)
    
    def solveRobot(self, url):
        import time
        import os
        
        dir_path = os.path.dirname(os.path.realpath(__file__))
        driver_filename = dir_path + "\chromedriver.exe"
        
        from selenium import webdriver
        from selenium.webdriver.common.keys import Keys
        driver = webdriver.Chrome(driver_filename)
        driver.get(url)
        
        while(1):
            time.sleep(10)
            webResponse = self.webSession.open(url)
    
            html = webResponse.read()
            html = unicode(html, 'utf-8')
            
            #Check if FA has blocked
            if "<title>Too many request</title>" not in html:
                break
    
    def getMovieInfoById(self, film):
        
        movieID = film.get_id()
        
        found = False
        intento = 0
        while found == False:
            if intento < 3:
                url = self.urlFilm + str(movieID) + self.urlFilmSufix
                webResponse = self.webSession.open(url)

                html = webResponse.read()
                #html = unicode(html, 'utf-8')
                
                if webResponse.getcode() != 200:
                    print(webResponse.getcode())
                    
                    intento = intento + 1
                    continue
                
                #Check if FA has blocked
                if "<title>Too many request</title>" in html:
                    self.solveRobot(url)
                    webResponse = self.webSession.open(url)

                    html = webResponse.read()
                    html = unicode(html, 'utf-8')
                    
                    if webResponse.getcode() != 200:
                        intento = intento + 1
                        continue
                
                # Get movie title information  
                soupPage = BeautifulSoup(html, 'html.parser')
                titleTag = soupPage.body.find('h1', attrs={'id': 'main-title'})
                
                if(titleTag==None):
                    print(
                    "ERROR FOUND: change regular expression at getMovieInfoById() for movie title. Probably FA changed web page structure. Movie ID: " + str(
                        movieID))
                    intento = intento + 1
                    continue
                
                else:
                    movieTitle = titleTag.text
                    movieTitle = movieTitle.replace("(TV Series)", "").strip()
                    movieTitle = movieTitle.replace("(TV)", "").strip()
                    movieTitle = movieTitle.replace("(S)", "").strip()                    
                    found = True
                
                # Get movie year information
                yearTag = soupPage.body.find('dd', attrs={'itemprop': 'datePublished'})
                
                if(yearTag==None):
                    print(
                        "ERROR FOUND: change regular expression at getMovieInfoById() for movie year. Probably FA changed web page structure. Movie ID: " + str(
                            movieID))
                    
                    intento = intento + 1
                    continue
                
                else:
                    movieYear = yearTag.text
                    
                # Get movie country information
                countryTag = soupPage.body.find('span', attrs={'id': 'country-img'})
                countryImageTag = countryTag.find('img', alt=True)
                
                if((countryTag == None) | (countryImageTag == None)):
                    print("ERROR FOUND: change regular expression at getMovieInfoById() for movie county. Probably FA changed web page structure. Movie ID: " + str(
                            movieID))
                else:
                    movieCountry = countryImageTag['alt']
               
                # Get movie director information
                movieDirector = ""
                directorTag = soupPage.body.find('dd', attrs={'class': 'directors'})
                
                if(directorTag==None):
                    print("ERROR FOUND: change regular expression at getMovieInfoById() for movie director. Probably FA changed web page structure. Movie ID: " + str(
                                movieID))
                                    
                else:
                    try:
                        movieDirector = directorTag.text
                    except AttributeError:
                        movieDirector = ""
                    
                    # clean the string
                    movieDirector = movieDirector.strip()
                    
                    while '  ' in movieDirector:
                        movieDirector = movieDirector.replace('  ', ' ')
                        movieDirector = movieDirector.replace('\n', '')
                        movieDirector = movieDirector.replace('\r', '')
                
                # Get movie cast information
                castTag = soupPage.body.find('span', attrs={'itemprop': 'actor'})
                
                try:
                    movieCast = castTag.parent.text
                except AttributeError:
                    movieCast = ""
                                
                # clean the string
                movieCast = movieCast.strip()
                while '  ' in movieCast:
                    movieCast = movieCast.replace('  ', ' ')
                    movieCast = movieCast.replace('\n', '')
                    movieCast = movieCast.replace('\r', '')
                
                # Get movie genre infomration
                genreTags = soupPage.body.find('span', attrs={'itemprop': 'genre'})
                
                try:
                    movieGenre = genreTags.parent.text
                except AttributeError:
                    movieGenre = ""
                
                # clean the string
                movieGenre = movieGenre.strip()
                while '  ' in movieGenre:
                    movieGenre = movieGenre.replace('  ', ' ')
                    movieGenre = movieGenre.replace('\n', '')
                    movieGenre = movieGenre.replace('\r', '')
                    
                # Get movie duration information
                durationTag = soupPage.body.find('dd', attrs={'itemprop': 'duration'})
                try:
                    movieDuration = durationTag.text
                except AttributeError:
                    movieDuration = ""
                
                # Get movie synopsis  information
                synopsisTag = soupPage.body.find('dd', attrs={'itemprop': 'description'})
                try:
                    movieSynopsis = synopsisTag.text
                    movieSynopsis = movieSynopsis.replace('  ', ' ')
                    movieSynopsis = movieSynopsis.replace('\n', '')
                    movieSynopsis = movieSynopsis.replace('\r', '')
                except AttributeError:
                    movieSynopsis = ""
                
        movieResult = self.FAMovieData(movieID=movieID, movieTitle=movieTitle, movieYear=movieYear,
                                               movieRate=film.movieRate, dayYYYYMMDD=film.dayYYYYMMDD)
        
        movieResult.set_movie_details(movieFaRate=film.movieFaRate, movieFaVotes=film.movieFaVotes, movieCountry=movieCountry, 
                                              movieDirector=movieDirector, movieCast=movieCast, movieGenre=movieGenre, movieDuration = movieDuration, movieSynopsis = movieSynopsis)
        
        film.set_movie_details(film.movieFaRate, film.movieFaVotes, movieCountry = movieCountry, movieDirector = movieDirector, movieCast = movieCast,
                                movieGenre = movieGenre, movieDuration = movieDuration, movieSynopsis = movieSynopsis)
        
        return movieResult

    def getMoviesDumped(self):
        return self.faMovies

    def getFilledMoviesDumped(self):
        return self.faMoviesFilled

    def getDumpAllVotes(self):
        numVotes, numPages = self.getNumVotes()
        print("FOUND: {0} movies in {1} pages.".format(numVotes, numPages))

        queue = Queue.Queue()
        for i in range(WORKERS):
            # FaVoteDumper(queue, self).start() # start a worker
            worker = FaVoteDumper(queue, self)
            worker.setDaemon(True)
            worker.start()

        for page in range(1, int(numPages) + 1):
            queue.put(page)
            
        if (int(numPages) == 0):
            queue.put(1)
        print("All pages pushed to queue!")

        for i in range(WORKERS):
            queue.put(None)  # add end-of-queue markers

        # Wait all threats of queue to finish
        queue.join()

        queueFill = Queue.Queue()
        for i in range(WORKERS):
            # FaFillInfo(queueFill, self).start() # start a worker
            worker = FaFillInfo(queueFill, self)
            worker.setDaemon(True)
            worker.start()

        for movie in self.faMovies:
            # print "Push movie: ", movie[0]
            queueFill.put(movie)
        print("\r\nAll movies pushed to queue to get all movie information.")

        for i in range(WORKERS):
            queueFill.put(None)  # add end-of-queue markers

        # Wait all threats of queueFill to finish
        queueFill.join()


class FaVoteDumper(threading.Thread):
    def __init__(self, queue, faHelp):
        self.__queue = queue
        threading.Thread.__init__(self)
        self.faHelp = faHelp

    def run(self):
        while 1:
            page = self.__queue.get()
            if page is None:
                self.__queue.task_done()
                break  # reached end of queue

            self.faHelp.getDumpVotesPage(page)
            print("Analyzed vote page: " +  str(page))
            self.__queue.task_done()


class FaFillInfo(threading.Thread):
    def __init__(self, queue, faHelp):
        self.__queue = queue
        threading.Thread.__init__(self)
        self.faHelp = faHelp

    def run(self):
        while 1:
            film = self.__queue.get()
            if film is None:
                self.__queue.task_done()
                break  # reached end of queue

            filmWithExtraInfo = self.faHelp.getMovieInfoById(film)

            self.faHelp.faMoviesFilled.append(filmWithExtraInfo)

            print("[FA get all data] ", filmWithExtraInfo.get_title())
            self.__queue.task_done()
