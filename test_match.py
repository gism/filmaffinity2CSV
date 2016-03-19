import unittest

import faHelper
import imdbHelper
import main
import time


def progress_format(total, current):
    return '{}/{}={}%'.format(current, total, 100 * current / total)
    pass


class Eta:
    def __init__(self, total):
        self._total = total
        self._init_time = time.time()
        pass

    def set_current(self, current):
        self._current = current

    def format(self):
        elapsed = (time.time() - self._init_time)
        tot_time = elapsed * self._total / self._current
        pend_time = tot_time - elapsed
        return '{} {}/{}'.format(progress_format(current=self._current, total=self._total), pend_time, tot_time)


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
    count = 0
    a1hits = 0
    a2hits = 0
    eta = Eta(len(fa_movies))
    for current_fa_movie in fa_movies:
        if False:
            alg1 = main.match_algorithm(imdb, current_fa_movie)
        else:
            alg1 = imdb.match_algorithm(current_fa_movie.movieTitle, current_fa_movie.movieYear)
        hcmc = main.hard_coded_matches.get(current_fa_movie.movieID)
        alg2 = imdb.match_algorithm_new(current_fa_movie.movieTitle, current_fa_movie.movieYear)
        alg1c = alg1.get_code()

        try:
            if hcmc is None:
                if alg2 is not None:
                    alg2c = alg2.get_code()
                    if alg1c == alg2c:
                        a1hits += 1
                        a2hits += 1
                    else:
                        print(
                            'ERROR: algorithms 1 and 2 do not match, please, add {} to hard coded match table to increase matching efficiency.'.format(
                                current_fa_movie.movieTitle))
                        assert False
                else:
                    # assuming it is right. Nothing to compare to.
                    a1hits += 1
            else:
                if alg2 is not None:
                    alg2c = alg2.get_code()
                    assert alg2c == hcmc
                    a2hits += 1
                else:
                    pass
                if alg1c == hcmc:
                    a1hits += 1
        except:
            raise
        count += 1
        eta.set_current(count)
        print(
            'progress={} alg1hits={} alg2hits={}'.format(eta.format(),
                                                         progress_format(current=a1hits, total=count),
                                                         progress_format(current=a2hits, total=count)))
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
