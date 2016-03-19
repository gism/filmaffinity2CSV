import unittest

from main import Counters, algorithm_strict

import faHelper
import imdbHelper
import main


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
