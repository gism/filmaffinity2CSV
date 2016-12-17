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
    urlVotesID = "http://www.filmaffinity.com/en/userratings.php?user_id="
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
        pattern = re.compile('Page <b>1<\/b> of <b>([\d]+)<\/b>')
        match = pattern.search(html)
        if match:
            numPages = match.group(1)
        else:
            print(
                "ERROR FOUND: change regular expression at getNumVotes() for numPages. Probably FA changed web page structure")
            sys.exit("Error happens, check log.")

        pattern = re.compile('<div class="number">([\d,\.]+)<\/div>[\r\n\s\t]+<div class="text">Votes<\/div>')
        match = pattern.search(html)
        if match:
            numVotes = match.group(1)
        else:
            print(
                "ERROR FOUND: change regular expression at getVotesByID() for numVotes. Probably FA changed web page structure")
            sys.exit("Error happens, check log.")

        return numVotes, numPages

    class FAMovieData:

        def __init__(self, movieID, movieTitle, movieYear, movieRate, dayYYYYMMDD):
            self.movieID = movieID
            self.movieTitle = movieTitle
            self.movieYear = movieYear
            self.movieRate = movieRate
            self.dayYYYYMMDD = dayYYYYMMDD

        def get_id(self):
            return self.movieID

        def get_title(self):
            return self.movieTitle

        def get_year(self):
            return self.movieYear

        def get_rate(self):
            return self.movieRate

        def set_extra_info(self, ei):
            self.extra_info = ei

        colum_names = ("ID", "Title", "Year", "Vote", "Voted", "Country", "Director", "Cast", "Genre")

        def tabulate1(self):
            return self.get_id(), self.get_title(), self.get_year(), self.movieRate, None, self.extra_info.movieCountry, self.extra_info.movieDirector, self.extra_info.movieCast, self.extra_info.movieGenre

    def getDumpVotesPage(self, page):

        if self.userId == "0":
            print("ERROR FOUND: No user id found. Please login or set user id.")
            sys.exit("Error happens, check log.")
            return

        url = self.urlVotesID + str(self.userId) + self.urlVotesIDpageSufix + str(page)
        webResponse = self.webSession.open(url)
        html = webResponse.read()
        html = unicode(html, 'utf-8')

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
                movieID = movie.find('div', attrs={'class': 'movie-card movie-card-0'}).get("data-movie-id")

                # Get movie rate
                movieRate = movie.find('div', attrs={'class': 'ur-mr-rat'}).text

                # Get title
                title = movie.find('div', attrs={'class': 'mc-title'})

                pattern = re.compile('\((\d\d\d\d)\)')
                match = pattern.search(title.text)
                if match:
                    movieYear = match.group(1)
                    movieTitle = title.text.replace("(" + movieYear + ")", "").strip()
                    movieTitle = movieTitle.replace("(TV Series)", "").strip()
                    movieTitle = movieTitle.replace("(TV)", "").strip()
                    movieTitle = movieTitle.replace("(S)", "").strip()
                else:
                    print(
                        "ERROR FOUND: change regular expression at getDumpVotesPage() for movie year. Probably FA changed web page structure")
                    sys.exit("Error happens, check log.")

                movieResult = self.FAMovieData(movieID=movieID, movieTitle=movieTitle, movieYear=movieYear,
                                               movieRate=movieRate, dayYYYYMMDD=dayYYYYMMDD)
                # print movieID, movieTitle, movieYear, movieRate, dayYYYYMMDD
                self.faMovies.append(movieResult)

    class FaMovieExtraInfo:
        def __init__(self, movieTitle, movieYear, movieCountry, movieDirector, movieCast, movieGenre):
            self.movieTitle = movieTitle
            self.movieYear = movieYear
            self.movieCountry = movieCountry
            self.movieDirector = movieDirector
            self.movieCast = movieCast
            self.movieGenre = movieGenre
        def __repr__(self):
            s = u"<FaMovieExtraInfo Title: {0}, Year: {1}, Country: {2} Director: {3}, Cast: {4}, Genre: {5}>".format(self.movieTitle, self.movieYear, self.movieCountry, self.movieDirector, self.movieCast, self.movieGenre)
            return s.encode('ascii', 'backslashreplace')
        
        def __str__(self):
            s = u"Title: {0}, Year: {1}, Country: {2} Director: {3}, Cast: {4}, Genre: {5}".format(self.movieTitle, self.movieYear, self.movieCountry, self.movieDirector, self.movieCast, self.movieGenre)
            return s.encode('ascii', 'backslashreplace')
        
    def getMovieInfoById(self, movieID):

        found = False
        intento = 0
        while found == False:
            if intento < 3:
                url = self.urlFilm + str(movieID) + self.urlFilmSufix
                webResponse = self.webSession.open(url)

                html = webResponse.read()
                html = unicode(html, 'utf-8')
                if webResponse.getcode() != 200:
                    print(webResponse.getcode())

                # Get movie title information
                pattern = re.compile('<span itemprop="name">([\w\W\s]+?)<\/span>')
                match = pattern.search(html)
                if match:
                    movieTitle = match.group(1)
                    movieTitle = movieTitle.replace("(TV Series)", "").strip()
                    movieTitle = movieTitle.replace("(TV)", "").strip()
                    movieTitle = movieTitle.replace("(S)", "").strip()                    
                    found = True
                else:
                    intento = intento + 1
            else:
                print(
                    "ERROR FOUND: change regular expression at getMovieInfoById() for movie title. Probably FA changed web page structure. Movie ID: " + str(
                        movieID))
                sys.exit("Error happens, check log.")

        # Get movie year information
        pattern = re.compile('<dt>Year<\/dt>[\s\r\n]+<dd[\w\W]+?>(\d\d\d\d)<\/dd>')
        match = pattern.search(html)
        if match:
            movieYear = match.group(1)
        else:
            print(
                "ERROR FOUND: change regular expression at getMovieInfoById() for movie year. Probably FA changed web page structure. Movie ID: " + str(
                    movieID))
            sys.exit("Error happens, check log.")

        # Get movie country information
        pattern = re.compile(
            '<dt>Country<\/dt>[\r\n\s]+<dd><span id="country-img"><[\W\w\s]+?><\/span>&nbsp;([\W\w\s]+?)<\/dd>')
        match = pattern.search(html)
        if match:
            movieCountry = match.group(1)
        else:
            print(
                "ERROR FOUND: change regular expression at getMovieInfoById() for movie county. Probably FA changed web page structure. Movie ID: " + str(
                    movieID))
            sys.exit("Error happens, check log.")

        # Get movie director information
        pattern = re.compile('<dt>Director<\/dt>[\w\s\W\r\n]+?<span itemprop="name">([\w\W\s]+?)<\/span>')
        match = pattern.search(html)
        if match:
            movieDirector = match.group(1)
            movieDirector = movieDirector.strip()
        else:
            print(
                "ERROR FOUND: change regular expression at getMovieInfoById() for movie director. Probably FA changed web page structure. Movie ID: " + str(
                    movieID))
            sys.exit("Error happens, check log.")

        # Get movie cast information
        pattern = re.compile('<dt>Cast<\/dt>[\s\r\n]+?<dd>([\w\W]+?)<\/dd>')
        match = pattern.search(html)
        if match:
            castWithLink = match.group(1)
            castWithLink = re.sub('<[\w\W\s\n\r]+?>', "", castWithLink)
            movieCast = re.sub('[\n\r]', "", castWithLink)
            movieCast = re.sub('[\s]+', " ", movieCast)
            movieCast = movieCast.strip()
        else:
            print(
                "ERROR FOUND: change regular expression at getMovieInfoById() for movie cast. Probably FA changed web page structure. Movie ID: " + str(
                    movieID))
            movieCast = "None"

        # Get movie genre infomration
        pattern = re.compile('<dt>Genre<\/dt>[\s\r\n]+?<dd>([\w\W]+?)<\/dd>')
        match = pattern.search(html)
        if match:
            genreWithLink = match.group(1)
            genreWithLink = re.sub('<[\w\W\s\n\r]+?>', "", genreWithLink)
            movieGenre = re.sub('[\n\r]', "", genreWithLink)
            movieGenre = re.sub('[\s]+', " ", movieGenre)
        else:
            print(
                "ERROR FOUND: change regular expression at getMovieInfoById() for movie genre. Probably FA changed web page structure. Movie ID: " + str(
                    movieID))
            sys.exit("Error happens, check log.")

        return self.FaMovieExtraInfo(movieTitle, movieYear, movieCountry, movieDirector, movieCast, movieGenre)

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
            print("Analyzing vote page: ", page)
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

            extraInfo = self.faHelp.getMovieInfoById(
                film.movieID)  # movieTitle, movieYear, movieCountry, movieDirector, movieCast, movieGenre
            film.set_extra_info(extraInfo)

            self.faHelp.faMoviesFilled.append(film)

            print("[FA get all data] ", film.get_title())
            self.__queue.task_done()
