import datetime
import unittest

import faHelper
import imdbHelper
import main


def progress_format(total, current):
    return '{}/{}={}%'.format(current, total, 100 * current / total)
    pass


class Eta:
    def __get_now(self):
        return datetime.datetime.now()

    def __init__(self, total):
        self._total = total
        self._init_time = self.__get_now()
        pass

    def set_current(self, current):
        self._current = current

    def format(self):
        elapsed = (self.__get_now() - self._init_time)
        tot_time = elapsed * self._total / self._current
        pend_time = tot_time - elapsed
        return '{} {}/{}'.format(progress_format(current=self._current, total=self._total), pend_time, tot_time)


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


def algorithm_strict(imdb, current_fa_movie, counters):
    alg1 = imdb.match_algorithm(current_fa_movie.movieTitle, current_fa_movie.movieYear)
    hcmc = main.hard_coded_matches.get(current_fa_movie.movieID)
    alg2 = imdb.match_algorithm_new(current_fa_movie.movieTitle, current_fa_movie.movieYear)

    found1 = alg1.could_match()
    found2 = alg2 is not None and alg2.could_match()
    strict = False
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
                if strict:
                    assert False

        else:
            pass

    pass
    return result


def algorithm_testing():
    """ This test tests both algorithms and makes sure that matches that are not the same in both
    have a hardcoded match to solve it.
    :return:
    """
    fa = faHelper.FAhelper()
    sUser, sPassword = main.ConfigManager.get_fa_user_pass()
    fa.login(sUser, sPassword)
    fa.getDumpAllVotes()
    fa_movies = fa.getMoviesDumped()
    imdb = imdbHelper.IMDBhelper()
    counters = Counters(len(fa_movies))
    for current_fa_movie in fa_movies:
        algorithm_strict(imdb, current_fa_movie, counters)
        counters.count += 1
        print(counters.format())
        pass
    pass


class TestMovieMatch(unittest.TestCase):
    def test_1(self):
        """
        algorithm should pass this test
        :return:
        """
        faHelp = faHelper.FAhelper()
        imdb = imdbHelper.IMDBhelper()

        for fa_code, imdb_code in main.hard_coded_matches.items():
            extraInfo = faHelp.getMovieInfoById(fa_code)
            current_fa_movie = extraInfo
            assert isinstance(current_fa_movie, faHelper.FAhelper.FaMovieExtraInfo)
            aaa = imdb.match_algorithm_new(current_fa_movie.movieTitle, current_fa_movie.movieYear)
            imdbID = imdb.match_algorithm(current_fa_movie.movieTitle, current_fa_movie.movieYear)
            if False:
                assert imdbID.get_code() == imdb_code
            assert aaa.get_code() == imdb_code
            pass

    def test_2(self):
        algorithm_testing()


if __name__ == "__main__":
    # unittest.main()
    # TestMovieMatch().test_2()
    algorithm_testing()
