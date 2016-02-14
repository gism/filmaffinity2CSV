# -*- coding: utf-8 -*-

import faHelper
import sys
from tabulate import tabulate
import codecs
import time
import imdbHelper
import threading, Queue
import re


class CountingQueue(Queue.Queue):
    def __init__(self, maxsize):
        # Queue.Queue.__init__(**locals())
        Queue.Queue.__init__(self, maxsize)
        self.__mycount = 0
        self.__total = 0

    def get(self):
        ret = Queue.Queue.get(self)
        self.__mycount += 1
        return ret

    def put(self, i):
        Queue.Queue.put(self, i)
        self.__total += 1

    def get_count(self):
        return self.__mycount

    def get_total(self):
        return self.__total


class FAMovieList:
    def __init__(self):
        self.__imdbNotFound = []

    def __len__(self):
        return len(self.__imdbNotFound)

    def empty(self):
        return len(self.__imdbNotFound) < 1

    def append(self, element):
        assert isinstance(element, faHelper.FAhelper.FAMovieData)
        self.__imdbNotFound.append(element)

    def saveAndPrint(self):
        imdbNotFound_tabulated = []
        for not_found_movie in self.__imdbNotFound:
            assert isinstance(not_found_movie, faHelper.FAhelper.FAMovieData)
            imdbNotFound_tabulated.append(not_found_movie.tabulate1())
        table_notFound = tabulate(imdbNotFound_tabulated,
                                  headers=list(faHelper.FAhelper.FAMovieData.colum_names),
                                  tablefmt='orgtbl')
        fileNameNotFound = "FilmsNotFoundAtIMDB" + "_" + str(tLocal.tm_year) + "-" + str(tLocal.tm_mon) + "-" + str(
            tLocal.tm_mday) + '-fauser' + fa.getUserID() + ".txt"
        fileNotFound = codecs.open(fileNameNotFound, "w", "utf_16")
        fileNotFound.write(table_notFound)
        fileNotFound.close()
        print("Movies not found:")
        print(table_notFound)


class MovieMatch:
    def __init__(self, fa, imdb):
        assert isinstance(fa, faHelper.FAhelper.FAMovieData)
        self.__fa = fa
        self.__imdb = imdb

    def fa(self):
        return self.__fa

    def imdb(self):
        return self.__imdb

    def tabulate1(self):
        # "ID fa:" + fa.getUserID() + "; ID imdb; Title; Year; Vote; Voted; Country; Director; Cast; Genre\n"
        a = self.__fa.tabulate1()
        b = list(a)
        b.insert(1, self.__imdb.get_code())
        return b

    @staticmethod
    def report_headers():
        b = list(faHelper.FAhelper.FAMovieData.colum_names)
        b.insert(1, "ID imdb")
        return b


class MatchedMoviesList:
    def __init__(self):
        self.__table = []

    def append(self, n):
        assert isinstance(n, MovieMatch)
        self.__table.append(n)

    def elements(self):
        return self.__table

    def __saveTableToCsv1(self):
        # Save movie list as CSV
        fileName = "FA-movies" + "_" + str(tLocal.tm_year) + "-" + str(tLocal.tm_mon) + "-" + str(
            tLocal.tm_mday) + '-fauser' + fa.getUserID() + ".csv"

        # with codecs.open(fileName, "w", "utf_16") as file1:
        with open(fileName, "w") as file1:
            writer = None
            for movie in self.__table:
                assert isinstance(movie, MovieMatch)
                if writer is None:
                    import unicodecsv as csv
                    writer = csv.writer(file1, encoding='utf-8')
                    writer.writerow(movie.report_headers())
                writer.writerow(movie.tabulate1())

    def __saveTableBeauty(self):
        tabulate_table = []
        for table_match in self.__table:
            assert isinstance(table_match, MovieMatch)
            tabulate_table.append(table_match.tabulate1())
        table_beautiful = tabulate(tabulate_table, headers=MovieMatch.report_headers(), tablefmt='orgtbl')
        fileNameBeauty = "FA-moviesBeauty" + "_" + str(tLocal.tm_year) + "-" + str(tLocal.tm_mon) + "-" + str(
            tLocal.tm_mday) + '-fauserid' + fa.getUserID() + ".txt"
        fileBeauty = codecs.open(fileNameBeauty, "w", "utf_16")
        fileBeauty.write(table_beautiful)
        fileBeauty.close()

    def saveTableToFiles(self):
        self.__saveTableToCsv1()
        self.__saveTableBeauty()


WORKERS = 4

start_time = time.time()
logo = '''
`7MM"""YMM  db               `7MMF'`7MMM.     ,MMF'`7MM"""Yb. `7MM"""Yp, 
  MM    `7 ;MM:                MM    MMMb    dPMM    MM    `Yb. MM    Yb 
  MM   d  ,V^MM.     pd*"*b.   MM    M YM   ,M MM    MM     `Mb MM    dP 
  MM""MM ,M  `MM    (O)   j8   MM    M  Mb  M' MM    MM      MM MM"""bg. 
  MM   Y AbmmmqMA       ,;j9   MM    M  YM.P'  MM    MM     ,MP MM    `Y 
  MM    A'     VML   ,-='      MM    M  `YM'   MM    MM    ,dP' MM    ,9 
.JMML..AMA.   .AMMA.Ammmmmmm .JMML..JML. `'  .JMML..JMMmmmdP' .JMMmmmd9                                                                
'''
print(logo)

tLocal = time.localtime()
fa = faHelper.FAhelper()

try:
    import config

    sUser = config.fauser
    sPassword = config.fapass
except:
    sUser = raw_input('Please enter your FilmAffinity USER:')
    sPassword = raw_input('Please enter your FilmAffinity PASSWORD:')

fa.setUser(sUser, sPassword)

# Option B: You want to hardcode your user and pass 
#    fa.setUser("Your USER", "Your PASSWORD")

# Option C: Hardcode your User ID
# fa.setUserID(123456)

fa.login()
if fa.loginSucceed():
    print("Login succeed")
else:
    print("Error on login")
    sys.exit("Not possible to finish task with no login")

print("Your FA ID is: ", fa.getUserID())

# if 0: ONLY for dev

# Download  
fa.getDumpAllVotes()
fatable = fa.getMoviesDumped()
match_result_table_2 = MatchedMoviesList()


def getImdbIdsThread(queue):
    while True:
        index = queue.get()
        if index is None:
            queue.task_done()
            break
        current_fa_movie = fatable[index]
        imdbID = imdb.getMovieCodeByAPI(current_fa_movie.get_title(), current_fa_movie.get_year())
        if imdbID.is_bad_match():
            imdbID = imdb.getMovieCode(current_fa_movie.get_title(), current_fa_movie.get_year())
        if imdbID.is_bad_match():
            t = re.sub('\([\w\W]*?\)', '', current_fa_movie.get_title()).strip()
            imdbID = imdb.getMovieCode(t, current_fa_movie.get_year())
        if imdbID.is_bad_match() or imdbID.get_code() == None:
            imdbNotFound.append(current_fa_movie)
        print("[Match IMDB] tt" + current_fa_movie.get_id(), "is: ", current_fa_movie.get_title(),
              " (" + current_fa_movie.get_year() + ")")

        # [current_fa_movie[0], imdbID[0].decode(), current_fa_movie[1], current_fa_movie[2], current_fa_movie[3], current_fa_movie[4], current_fa_movie[5], current_fa_movie[6], current_fa_movie[7], current_fa_movie[8]]
        match_result_table_2.append(MovieMatch(current_fa_movie, imdbID))
        if index % 10 == 0:
            print("Task progress: " + str(index) + "/" + str(len(fatable)) + " (" + str(
                index * 100 / float(len(fatable)))[
                                                                                    :5] + "%)")
        queue.task_done()


def voteImdbThread(queue):
    while True:
        movie_match = queue.get()
        if movie_match is None:
            queue.task_done()
            break
        assert isinstance(movie_match, MovieMatch)
        try:
            if not movie_match.imdb().is_bad_match():
                imdb.voteMovie(movie_match.imdb().get_code_decoded(), movie_match.fa().get_rate())
        except:
            e = sys.exc_info()
            imdbNotVoted.append(movie_match)
            print("ERROR: en pelicula", movie_match.imdb().get_code_decoded(), movie_match.fa().get_title())
        index = queue.get_count()
        if index % 10 == 0:
            print("Task progress: " + str(index) + "/" + str(queue.get_total()) + " (" + str(
                index * 100 / float(queue.get_total()))[:5] + "%)")
        queue.task_done()


try:
    import config

    backuptoimdb = config.backuptoimdb
except:
    sIn = raw_input('\r\nDo you want to backup to IMDB? <Y> or <N>:')
    while (sIn.lower() != "y" and sIn.lower() != "n"):
        sIn = raw_input('Do you want to backup to IMDB? <Y> or <N>:')
    if sIn.lower() == "y":
        backuptoimdb = True
    else:
        backuptoimdb = False

if backuptoimdb:
    imdb = imdbHelper.IMDBhelper()

    # Cola con las pelis para obterner el codigo de pelicula en IMDB    
    q = Queue.Queue()
    # Array para las peliculas que presenten peliculas
    imdbNotFound = FAMovieList()
    imdbNotVoted = []

    # Start multi-thread. One thread for each worker, all use same queue.
    threads = []
    for i in range(WORKERS):
        worker = threading.Thread(target=getImdbIdsThread, args=(q,))
        worker.setDaemon(True)
        worker.start()
        threads.append(worker)

    # Enqueue all movies in queue
    for i in range(len(fatable)):
        q.put(i)

    for i in range(WORKERS):
        q.put(None)  # add end-of-queue markers

    # Wait threads and workers to finish
    q.join()

    if not imdbNotFound.empty():
        print("\r\nCaution: ", len(imdbNotFound), " FA movies could not be fount in IMDB!")
        imdbNotFound.saveAndPrint()

    print("\r\nAll movies from FA matched with IMDB database.\r\n")
    print("--- Total runtime %s seconds ---" % (time.time() - start_time))

    # Option A: You want to write each time User and Password:
    try:
        import config

        sUser = config.imdb_user
        sPassword = config.imdb_password
    except:
        sUser = raw_input('Please enter your FilmAffinity USER:')
        sPassword = raw_input('Please enter your FilmAffinity PASSWORD:')
    imdb.setUser(sUser, sPassword)

    # Option B: You want to hardcode your user and pass
    # imdb.setUser("user@gmail.com", "imdb_pass")

    # Login to IMDB
    imdb.login()
    while not imdb.loginSucceed():
        imdb.login()
    print("Login succeed")
    qVotes = CountingQueue(maxsize=0)

    for i in range(WORKERS):
        voter = threading.Thread(target=voteImdbThread, args=(qVotes,))
        voter.setDaemon(True)
        voter.start()

    for i in match_result_table_2.elements():
        qVotes.put(i)

    for i in range(WORKERS):
        q.put(None)  # add end-of-queue markers

    qVotes.join()

    if len(imdbNotVoted) > 0:
        assert isinstance(imdbNotVoted[0], MovieMatch)
        print("\r\nCaution: It was not possible to vote ", len(imdbNotVoted), " movies",
              ' (fa: ' + fa.getUserID() + ')')
        blo = []
        for a in imdbNotVoted:
            assert isinstance(a, MovieMatch)
            blo.append(a.tabulate1())
        # Write table with format
        try:
            table_notVoted = tabulate(blo, headers=MovieMatch.report_headers(), tablefmt='orgtbl')
        except:
            raise
        fileNameNotVoted = "FilmsNotVotedAtIMDB" + "_" + str(tLocal.tm_year) + "-" + str(tLocal.tm_mon) + "-" + str(
            tLocal.tm_mday) + '-fauser' + fa.getUserID() + ".txt"
        fileNotVoted = codecs.open(fileNameNotVoted, "w", "utf_16")
        fileNotVoted.write(table_notVoted)
        fileNotVoted.close()
        print("Movies not voted:")
        print(table_notVoted)

match_result_table_2.saveTableToFiles()

print("--- Total runtime %s seconds ---" % (time.time() - start_time))
print("\r\nDONE")
