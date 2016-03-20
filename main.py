# -*- coding: utf-8 -*-

import codecs
import sys
import time
from tabulate import tabulate

import faHelper
import imdbHelper
from common import CountingQueue, createTrheadedQueue
from common import progress_format, Eta
import logging


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

    def saveReport(self, prefix, postfix):
        imdbNotFound_tabulated = []
        for not_found_movie in self.__imdbNotFound:
            assert isinstance(not_found_movie, faHelper.FAhelper.FAMovieData)
            imdbNotFound_tabulated.append(not_found_movie.report_attr_values())
        table_notFound = tabulate(imdbNotFound_tabulated,
                                  headers=list(faHelper.FAhelper.FAMovieData.report_attr_names),
                                  tablefmt='orgtbl')

        tLocal = time.localtime()
        fileNameNotFound = prefix + "_" + str(tLocal.tm_year) + "-" + str(tLocal.tm_mon) + "-" + str(
            tLocal.tm_mday) + postfix + ".txt"
        fileNotFound = codecs.open(fileNameNotFound, "w", "utf_16")
        fileNotFound.write(table_notFound)
        fileNotFound.close()
        return table_notFound


class MovieMatch:
    def __init__(self, fa, imdb):
        assert isinstance(fa, faHelper.FAhelper.FAMovieData)
        self.__fa = fa
        try:
            assert imdb is None or isinstance(imdb, imdbHelper.IMDBhelper.ImdbFoundMovie)
        except:
            raise
        self.__imdb = imdb

    def fa(self):
        return self.__fa

    def imdb(self):
        return self.__imdb

    def __imdb_get_year(self):
        if self.__imdb is not None:
            return self.__imdb.get_year()
        else:
            return None

    def __imdb_get_title(self):
        if self.__imdb is not None:
            return self.__imdb.get_title()
        else:
            return None

    def __imdb_get_title_ratio(self):
        if self.__imdb is not None:
            return self.__imdb.get_title_ratio()
        else:
            return None

    def __imdb_get_result(self):
        if self.__imdb is not None:
            return self.__imdb.get_result()
        else:
            return None

    def __imdb_get_code(self):
        if self.__imdb is not None:
            return self.__imdb.get_code()
        else:
            return None

    def __imdb_get_url(self):
        if self.__imdb is not None:
            return self.__imdb.get_url()
        else:
            return None

    def report(self):
        fa_fields = self.__fa.report_attr_values()
        fa_fields_in_list = list(fa_fields)
        fa_fields_in_list.insert(3, self.__imdb_get_year())
        fa_fields_in_list.insert(2, self.__imdb_get_title())
        fa_fields_in_list.insert(1, self.__imdb_get_title_ratio())
        fa_fields_in_list.insert(1, self.__imdb_get_result())
        fa_fields_in_list.insert(1, self.__imdb_get_code())
        fa_fields_in_list.append(self.__imdb_get_url())
        return fa_fields_in_list

    @staticmethod
    def report_headers():
        b = list(faHelper.FAhelper.FAMovieData.report_attr_names)
        b.insert(3, "imdb year")
        b.insert(2, "imdb title")
        b.insert(1, "imdb ratio")
        b.insert(1, "imdb match")
        b.insert(1, "imdb code")
        b.append('imdb url')
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


# these movies failed with first algorithm. We will try ti build an algorithm that does not make this failures.
hard_coded_matches = {'809297': 'tt0068646', '573847': 'tt0276919', '509573': 'tt0970416', '346540': 'tt0099674',
                      '731920': 'tt0067800', '670216': 'tt2562232', '846099': 'tt3659388', '224676': 'tt3605418',
                      '264280': 'tt3626742', '545095': 'tt1971325', '220999': 'tt2668134', '890034': 'tt0756683',
                      '540303': 'tt3276924', '961632': 'tt3510480', '695552': 'tt0050083', '690533': 'tt1524930',
                      '652874': 'tt3495184', '375978': 'tt2089050', '701892': 'tt0078788', '224676': 'tt3605418',
                      '695552': 'tt0050083', '612331': 'tt0079470', '568510': 'tt0208092', '750188': 'tt0111301',
                      '645363': 'tt0246578', '662169': 'tt0434409', '577638': 'tt0118655', '332725': 'tt0945513',
                      '152490': 'tt0107290', '462892': 'tt0093058', '867354': 'tt0468569', '307437': 'tt0245612',
                      '662342': 'tt0388795', '745914': 'tt1028528', '633995': 'tt0120611', '151039': 'tt0211915',
                      '968175': 'tt0378194', '495280': 'tt0499549', '893272': 'tt0099653', '489970': 'tt0903747',
                      '152408': 'tt4412362', '828416': 'tt0993846', '533016': 'tt0116996', '267203': 'tt2823088',
                      '520253': 'tt1951265', '524439': 'tt0266697', '837017': 'tt2089051', '971380': 'tt1375666',
                      '453359': 'tt2170593', '375488': 'tt1502712'}


class Counters:
    def __init__(self, total):
        self.a1hits = 0
        self.a2hits = 0
        self.count = 0
        self.eta = Eta(total)

    def format(self):
        self.eta.set_current(self.count)
        return 'progress={} alg1hits={} alg2hits={}'.format(self.eta.format(),
                                                            progress_format(current=self.a1hits, total=self.count),
                                                            progress_format(current=self.a2hits, total=self.count))


def match_algorithm_merge_strict(imdb, current_fa_movie, counters):
    if current_fa_movie.get_id() == '652874':
        pass
    alg1 = imdb.match_algorithm(current_fa_movie.movieTitle, current_fa_movie.movieYear)
    hcmc = hard_coded_matches.get(current_fa_movie.movieID)
    alg2 = imdb.match_algorithm_new(current_fa_movie.movieTitle, current_fa_movie.movieYear)

    found1 = alg1.could_match()
    found2 = alg2 is not None and alg2.could_match()
    strict = True
    result = None
    if hcmc is None:

        if found1:
            counters.a1hits += 1
            result = alg1
        else:
            pass

        if found2:
            counters.a2hits += 1
            result = alg2
        else:
            pass

        if found1 and found2 and not alg1.get_code() == alg2.get_code():
            print(
                'ERROR: algorithms 1 and 2 do not match, please, add {} to hard coded match table to increase matching efficiency.'.format(
                    current_fa_movie.movieTitle))
            if strict:
                assert False
    else:

        if found1:
            if alg1.get_code() == hcmc:
                counters.a1hits += 1
                result = alg1
            else:
                pass

        if found2:
            if alg2.get_code() == hcmc:
                counters.a2hits += 1
                result = alg2
            else:
                if result is None:
                    pass
                    if strict:
                        assert False

        else:
            pass

        if result == None:
            result = imdb.get_from_code(hcmc, current_fa_movie.movieTitle, current_fa_movie.movieYear)

    pass
    return result


def match_algorithm_1(imdb, current_fa_movie):
    assert isinstance(current_fa_movie, faHelper.FAhelper.FAMovieData)
    fa_id = current_fa_movie.get_id()
    if fa_id == '809297':
        pass
    imdbID = imdb.match_algorithm(current_fa_movie.get_title(), current_fa_movie.get_year())

    use_hard_coded_matches = True
    if use_hard_coded_matches:
        if fa_id in hard_coded_matches:
            imdbID = imdb.get_from_code(hard_coded_matches[fa_id])
    return imdbID


class Algorithms:
    ALG1 = 'alg1'
    ALG2 = 'alg2'
    MERGESTRICT = 'mergestrict'
    ALL = [ALG1, ALG2]


def movie_match(current_fa_movie, imdb, match_results, imdbNotFound, alg):
    assert isinstance(current_fa_movie, faHelper.FAhelper.FAMovieData)

    if alg == Algorithms.ALG1:
        imdbID = match_algorithm_1(imdb, current_fa_movie)
    elif alg == Algorithms.MERGESTRICT:
        imdbID = match_algorithm_merge_strict(imdb, current_fa_movie, Counters(1))
    else:
        raise NotImplementedError()

    if imdbID is None or imdbID.is_bad_match() or imdbID.get_code() == None:
        imdbNotFound.append(current_fa_movie)

    print("[Match IMDB] tt" + current_fa_movie.get_id() + " is: " + current_fa_movie.get_title() +
          " (" + current_fa_movie.get_year() + ")")

    match_results.append(MovieMatch(current_fa_movie, imdbID))


def getImdbIdsThread(queue, imdb, imdbNotFound, match_results, alg):
    assert isinstance(queue, CountingQueue)
    while True:
        current_fa_movie = queue.get()
        if current_fa_movie is None:
            queue.task_done()
            break
        movie_match(current_fa_movie, imdb, match_results, imdbNotFound, alg)
        if queue.get_count() % 10 == 0:
            print("Task progress: " + queue.get_progress_desc())
        queue.task_done()


def voteImdbThread(queue, imdb, imdbNotVoted):
    while True:
        movie_match = queue.get()
        if movie_match is None:
            queue.task_done()
            break
        assert isinstance(movie_match, MovieMatch)
        try:
            if not movie_match.imdb().bad_or_no_match():
                imdb.voteMovie(movie_match.imdb().get_code_decoded(), movie_match.fa().get_rate())
        except:
            msg = "ERROR: en pelicula {} {}".format(movie_match.imdb().get_code_decoded(), movie_match.fa().get_title())
            e = sys.exc_info()
            logging.exception(msg)
            imdbNotVoted.append(movie_match)
            print(msg)
        index = queue.get_count()
        if index % 10 == 0:
            print("Task progress: " + queue.get_progress_desc())
        queue.task_done()


class ConfigManager:
    @classmethod
    def get_imdb_user_pass(cls):
        pass
        try:
            import config

            sUser = config.imdb_user
            sPassword = config.imdb_password
        except:
            sUser = raw_input('Please enter your FilmAffinity USER:')
            sPassword = raw_input('Please enter your FilmAffinity PASSWORD:')
        return sUser, sPassword

    @classmethod
    def get_fa_user_pass(cls):
        try:
            import config

            sUser = config.fauser
            sPassword = config.fapass
        except:
            sUser = raw_input('Please enter your FilmAffinity USER:')
            sPassword = raw_input('Please enter your FilmAffinity PASSWORD:')
        return sUser, sPassword

    @classmethod
    def match_with_imdb(cls):
        try:
            import config

            backuptoimdb = config.matchwithimdb
        except:
            msg = 'Do you want to match with IMDB? <Y> or <N>:'
            sIn = raw_input('\r\n{}'.format(msg))
            while (sIn.lower() != "y" and sIn.lower() != "n"):
                sIn = raw_input(msg)
            if sIn.lower() == "y":
                backuptoimdb = True
            else:
                backuptoimdb = False
        return backuptoimdb

    @classmethod
    def copy_votes_to_imdb(cls):
        try:
            import config

            backuptoimdb = config.backuptoimdb
        except:
            msg = 'Do you want to backup to IMDB? <Y> or <N>:'
            sIn = raw_input('\r\n{}:'.format(msg))
            while (sIn.lower() != "y" and sIn.lower() != "n"):
                sIn = raw_input(msg)
            if sIn.lower() == "y":
                backuptoimdb = True
            else:
                backuptoimdb = False
        return backuptoimdb

    @classmethod
    def algorithm(cls):
        try:
            import config

            algorithm = config.algorithm
        except:
            msg = 'Witch algoritm do you wiant to use? {}:'.format(Algorithms.ALL)
            algorithm = raw_input('\r\n{}:'.format(msg))
        return algorithm


def copy_votes_from_fa_to_imdb(imdb, match_results, postfix):
    imdbNotVoted = MatchedMoviesList()
    # Option A: You want to write each time User and Password:
    sUser, sPassword = ConfigManager.get_imdb_user_pass()

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
              ' (' + postfix + ')')
        table_notVoted = imdbNotVoted.saveReportBeauty("FilmsNotVotedAtIMDB", postfix)
        print("Movies not voted:")
        print(table_notVoted)


def match_fa_with_imdb(fa_movies, start_time, report_postfix, threaded):
    match_results = MatchedMoviesList()
    imdb = imdbHelper.IMDBhelper()
    imdbNotFound = FAMovieList()

    print('\nAbout to get imdb ids...\n')

    alg = ConfigManager.algorithm()
    if threaded:
        createTrheadedQueue(target=getImdbIdsThread, args=(imdb, imdbNotFound, match_results, alg),
                            elements=fa_movies)
    else:
        for current_fa_movie in fa_movies:
            movie_match(current_fa_movie, imdb, match_results, imdbNotFound, alg)

    if not imdbNotFound.empty():
        print("\r\nCaution: ", len(imdbNotFound), " FA movies could not be fount in IMDB!")
        table_notFound = imdbNotFound.saveReport("FilmsNotFoundAtIMDB", report_postfix)
        print("Movies not found:")
        print(table_notFound)

    print("\r\nAll movies from FA matched with IMDB database.\r\n")
    print("--- Total runtime %s seconds ---" % (time.time() - start_time))

    if ConfigManager.copy_votes_to_imdb():
        copy_votes_from_fa_to_imdb(imdb, match_results, report_postfix)
    return match_results


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

    fa = faHelper.FAhelper()
    sUser, sPassword = ConfigManager.get_fa_user_pass()
    fa.login(sUser, sPassword)
    if fa.loginSucceed():
        print("Login succeed")
    else:
        print("Error on login")
        sys.exit("Not possible to finish task with no login")

    print("Your FA ID is: {}".format(fa.getUserID()))

    fa.getDumpAllVotes()

    if ConfigManager.match_with_imdb():
        match_results = match_fa_with_imdb(fa.getMoviesDumped(), start_time, '-fauser' + fa.getUserID(), threaded=True)
        match_results.saveCsvReportAndBeauty("FA-movies", "FA-moviesBeauty", '-fauserid' + fa.getUserID())

    print("--- Total runtime %s seconds ---" % (time.time() - start_time))
    print("\r\nDONE")


if __name__ == "__main__":
    main()
