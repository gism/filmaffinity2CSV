import unittest

from main import MatchAlgorithms

import faHelper
import imdbHelper
import main


def match_algorithm_efficiency_testing_2():
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
    counters = MatchAlgorithms.Counters(len(fa_movies))
    for current_fa_movie in fa_movies:
        MatchAlgorithms.match_algorithm_merge_strict(imdb, current_fa_movie, counters)
        counters.count += 1
        print(counters.format())
        pass
    pass


def imdb_votes():
    imdb = imdbHelper.IMDBhelper()
    sUser, sPassword = main.ConfigManager.get_imdb_user_pass()
    imdb.setUser(sUser, sPassword)
    # Login to IMDB
    imdb.login()
    votes = imdb.votes()
    votes2 = list(votes)
    pass


class TestMovieMatch(unittest.TestCase):
    def test_1_match_algorithms(self):
        """
        algorithm should pass this test
        :return:
        """
        faHelp = faHelper.FAhelper()
        imdb = imdbHelper.IMDBhelper()

        for fa_code, imdb_code in main.MatchAlgorithms.hard_coded_matches.items():
            extraInfo = faHelp.getMovieInfoById(fa_code)
            current_fa_movie = extraInfo
            assert isinstance(current_fa_movie, faHelper.FAhelper.FaMovieExtraInfo)
            algorithm_1_result = main.MatchAlgorithms.match_algorithm_1(imdb, current_fa_movie)
            algorithm_2_result = main.MatchAlgorithms.match_algorithm_2(imdb, current_fa_movie)
            if False:
                assert algorithm_1_result.get_code() == imdb_code
            assert algorithm_2_result.get_code() == imdb_code
            pass

    def test_2_match_algorithms_efficiency(self):
        match_algorithm_efficiency_testing_2()

    @unittest.skip("it is not non-interactive.")
    def test_3(self):
        imdb_votes()


if __name__ == "__main__":
    # unittest.main()
    # TestMovieMatch().test_2()
    if True:
        match_algorithm_efficiency_testing_2()
    else:
        imdb_votes()
