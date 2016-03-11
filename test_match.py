import unittest

import faHelper
import imdbHelper
import match


class TestMovieMatch(unittest.TestCase):
    def test_1(self):
        """
        algorithm should pass this test
        :return:
        """
        faHelp = faHelper.FAhelper()
        imdb = imdbHelper.IMDBhelper()

        for fa_code, imdb_code in match.hard_coded_matches.items():
            extraInfo = faHelp.getMovieInfoById(fa_code)
            current_fa_movie = extraInfo
            assert isinstance(current_fa_movie, faHelper.FAhelper.FaMovieExtraInfo)
            imdbID = imdb.match_alg_2(current_fa_movie.movieTitle, current_fa_movie.movieYear)
            assert imdbID.get_code() == imdb_code
            pass
