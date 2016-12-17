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
    def __init__(self, maxsize=0):
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


def createTrheadedQueue(target, args, elements):
    WORKERS = 4
    q = CountingQueue()
    # Start multi-thread. One thread for each worker, all use same queue.
    threads = []
    newargs = (q,) + args
    for i in range(WORKERS):
        worker = threading.Thread(target=target, args=newargs)
        worker.setDaemon(True)
        worker.start()
        threads.append(worker)

    # Enqueue all movies in queue
    for i in elements:
        q.put(i)

    for i in range(WORKERS):
        q.put(None)  # add end-of-queue markers

    # Wait threads and workers to finish
    q.join()


class FAMovieList:
    def __init__(self):
        self.__movieTable = []

    def __len__(self):
        return len(self.__movieTable)

    def empty(self):
        return len(self.__movieTable) < 1

    def append(self, element):
        assert isinstance(element, faHelper.FAhelper.FAMovieData)
        self.__movieTable.append(element)

    def saveReport(self, fileName):
        movieTable_tabulated = []
        for movie in self.__movieTable:
            assert isinstance(movie, faHelper.FAhelper.FAMovieData)
            movieTable_tabulated.append(movie.tabulate1())
        table_acii = tabulate(movieTable_tabulated,
                                  headers=list(faHelper.FAhelper.FAMovieData.colum_names),
                                  tablefmt='orgtbl')
        
        tableFile = codecs.open(fileName, "w", "utf_16")
        tableFile.write(table_acii)
        tableFile.close()
        return table_acii
    
    def saveCSV(self, fileName):
        csv = u''
        for movie in self.__movieTable:
            for a in movie.tabulate1():
                if a == None: a =""
                a = a.replace(";", ",")
                csv = csv + a + ";"
            csv = csv + "\n"
            
        csvFile = codecs.open(fileName, "w", "utf_16")
        csvFile.write(csv)
        csvFile.close()
        return csv

class MovieMatch:
    def __init__(self, fa, imdb):
        assert isinstance(fa, faHelper.FAhelper.FAMovieData)
        self.__fa = fa
        assert isinstance(imdb, imdbHelper.IMDBhelper.ImdbFoundMovie)
        self.__imdb = imdb

    def fa(self):
        return self.__fa

    def imdb(self):
        return self.__imdb

    def report(self):
        fa_fields = self.__fa.tabulate1()
        fa_fields_in_list = list(fa_fields)
        fa_fields_in_list.insert(3, self.__imdb.get_year())
        fa_fields_in_list.insert(2, self.__imdb.get_title())
        fa_fields_in_list.insert(1, self.__imdb.get_ratio())
        fa_fields_in_list.insert(1, self.__imdb.get_result())
        fa_fields_in_list.insert(1, self.__imdb.get_code())
        return fa_fields_in_list

    @staticmethod
    def report_headers():
        b = list(faHelper.FAhelper.FAMovieData.colum_names)
        b.insert(3, "imdb year")
        b.insert(2, "imdb title")
        b.insert(1, "imdb ratio")
        b.insert(1, "imdb match")
        b.insert(1, "imdb code")
        return b


class MatchedMoviesList:
    def __init__(self):
        self.__table = []

    def __len__(self):
        return len(self.__table)

    def append(self, n):
        assert isinstance(n, MovieMatch)
        self.__table.append(n)

    def elements(self):
        return self.__table

    def __saveTableToCsv1(self, csvprefix, postfix):
        # Save movie list as CSV
        tLocal = time.localtime()
        fileName = csvprefix + "_" + str(tLocal.tm_year) + "-" + str(tLocal.tm_mon) + "-" + str(
            tLocal.tm_mday) + postfix + ".csv"

        # with codecs.open(fileName, "w", "utf_16") as file1:
        with open(fileName, "w") as file1:
            writer = None
            for movie in self.__table:
                assert isinstance(movie, MovieMatch)
                if writer is None:
                    import unicodecsv as csv
                    writer = csv.writer(file1, encoding='utf-8')
                    writer.writerow(movie.report_headers())
                writer.writerow(movie.report())

    def __build_tab_report(self):
        tabulate_table = []
        for table_match in self.__table:
            assert isinstance(table_match, MovieMatch)
            tabulate_table.append(table_match.report())
        table_beautiful = tabulate(tabulate_table, headers=MovieMatch.report_headers(), tablefmt='orgtbl')
        return table_beautiful

    def __saveTableBeauty(self, beautyprefix, postfix):
        table_beautiful = self.__build_tab_report()
        tLocal = time.localtime()
        fileNameBeauty = beautyprefix + "_" + str(tLocal.tm_year) + "-" + str(tLocal.tm_mon) + "-" + str(
            tLocal.tm_mday) + postfix + ".txt"
        fileBeauty = codecs.open(fileNameBeauty, "w", "utf_16")
        fileBeauty.write(table_beautiful)
        fileBeauty.close()
        return table_beautiful

    def saveCsvReportAndBeauty(self, csvprefix, beautyprefix, postfix):
        self.__saveTableToCsv1(csvprefix, postfix)
        self.__saveTableBeauty(beautyprefix, postfix)

    def saveReportBeauty(self, prefix, postfix):
        table_notVoted = self.__saveTableBeauty(prefix, postfix)
        return table_notVoted


def getImdbIdsThread(queue, imdb, imdbNotFound, match_results):
    assert isinstance(queue, CountingQueue)
    while True:
        current_fa_movie = queue.get()
        if current_fa_movie is None:
            queue.task_done()
            break
        assert isinstance(current_fa_movie, faHelper.FAhelper.FAMovieData)
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

        match_results.append(MovieMatch(current_fa_movie, imdbID))
        if queue.get_count() % 10 == 0:
            print("Task progress: " + str(queue.get_count()) + "/" + str(queue.get_total()) + " (" + str(
                queue.get_count() * 100 / float(queue.get_total()))[:5] + "%)")
        queue.task_done()


def voteImdbThread(queue, imdb, imdbNotVoted):
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


def main():
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
    
    # Create a FilmAfinity handler
    fa = faHelper.FAhelper()
    sUser_id = ""
    try:
        # Configuration file is not mandatory (just to avoid introducing credentials each run)
        import config
        sUser = config.fauser
        sPassword = config.fapass
        sUser_id = config.fauser_id
    except:
        sIn = raw_input('\r\nDo you know your FilmAffinity User ID? <Y> or <N>:')
        while (sIn.lower() != "y" and sIn.lower() != "n"):
            sIn = raw_input('Do you know your FilmAffinity User ID? <Y> or <N>:')
        if sIn.lower() == "y":
            sUser_id = raw_input('Introduce user ID:')
        else:
            sUser = raw_input('Please enter your FilmAffinity USER:')
            sPassword = raw_input('Please enter your FilmAffinity PASSWORD:')
    
    if  (sUser_id == "" or (not sUser_id.isdigit())):
        fa.setUser(sUser, sPassword)
        fa.login()
        if fa.loginSucceed():
            print("Login succeed")
        else:
            print("Error on login")
            sys.exit("Not possible to finish task with no login")
        print("Your FA ID is: ", fa.getUserID())
    else:
        fa.setUserID(sUser_id)
    
    
    fa.getDumpAllVotes()
    fa_movies = fa.getMoviesDumped()
    match_results = MatchedMoviesList()
    
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
        
    if not backuptoimdb:
        # Save file with all FA information
        listFaMovies = FAMovieList()
        for movie in fa_movies:
            listFaMovies.append(movie)
        tLocal = time.localtime()
        tableFileName = "FA_" + str(tLocal.tm_year) + "_" + str(tLocal.tm_mon) + "_" + str(tLocal.tm_mday) + '_fauser' + fa.getUserID() + ".txt"
        table_ascii = listFaMovies.saveReport(tableFileName)
        print("FilmAffinity movie list (TXT) saved at: " + tableFileName)
        csvFileName = "FA_" + str(tLocal.tm_year) + "_" + str(tLocal.tm_mon) + "_" + str(tLocal.tm_mday) + '_fauser' + fa.getUserID() + ".csv"
        listFaMovies.saveCSV(csvFileName)
        print("FilmAffinity movie list (CSV) saved at: " + csvFileName)
        print(table_ascii)
            
    else:
        # Transfer FA votes to IMDB:
        imdb = imdbHelper.IMDBhelper()

        # Array para las peliculas que presenten peliculas
        imdbNotFound = FAMovieList()
        imdbNotVoted = MatchedMoviesList()

        # Cola con las pelis para obterner el codigo de pelicula en IMDB
        print('\nAbout to get imdb ids...\n')
        createTrheadedQueue(target=getImdbIdsThread, args=(imdb, imdbNotFound, match_results),
                            elements=fa_movies)

        if not imdbNotFound.empty():
            print("\r\nCaution: ", len(imdbNotFound), " FA movies could not be fount in IMDB!")
            tLocal = time.localtime()
            tableFileName = "FilmsNotFoundAtIMDB_" + str(tLocal.tm_year) + "_" + str(tLocal.tm_mon) + "_" + str(tLocal.tm_mday) + '_fauser' + fa.getUserID() + ".txt"
            table_notFound = imdbNotFound.saveReport(tableFileName)
            print("Movies not found:")
            print(table_notFound)

        print("\r\nAll movies from FA matched with IMDB database.\r\n")
        print("--- Total runtime %s seconds ---" % (time.time() - start_time))

        try:
            import config
            sUser = config.imdb_user
            sPassword = config.imdb_password
        except:
            sUser = raw_input('Please enter your FilmAffinity USER:')
            sPassword = raw_input('Please enter your FilmAffinity PASSWORD:')
        imdb.setUser(sUser, sPassword)

        # Login to IMDB
        imdb.login()
        while not imdb.loginSucceed():
            imdb.login()
        print("Login succeed")
        createTrheadedQueue(target=voteImdbThread, args=(imdb, imdbNotVoted),
                            elements=match_results.elements())

        if len(imdbNotVoted) > 0:
            print("\r\nCaution: It was not possible to vote ", len(imdbNotVoted), " movies",
                  ' (fa: ' + fa.getUserID() + ')')
            table_notVoted = imdbNotVoted.saveReportBeauty("FilmsNotVotedAtIMDB", '-fauser' + fa.getUserID())
            print("Movies not voted:")
            print(table_notVoted)
    
        match_results.saveCsvReportAndBeauty("FA-movies", "FA-moviesBeauty", '-fauserid' + fa.getUserID())
        
    print("--- Total runtime %s seconds ---" % (time.time() - start_time))
    print("\r\nDONE")


main()
