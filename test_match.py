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
            aaa = imdb.match_algorithm_new(current_fa_movie.movieTitle, current_fa_movie.movieYear)
            imdbID = imdb.match_algorithm(current_fa_movie.movieTitle, current_fa_movie.movieYear)
            if False:
                assert imdbID.get_code() == imdb_code
            assert aaa.get_code() == imdb_code
            pass

    def test_2(self):
        fa = faHelper.FAhelper()
        import main
        import match
        sUser, sPassword = main.ConfigManager.get_fa_user_pass()
        fa.login(sUser, sPassword)
        fa.getDumpAllVotes()
        fa_movies = fa.getMoviesDumped()
        imdb = imdbHelper.IMDBhelper()
        count = 0
        a1hits = 0
        a2hits = 0
        for current_fa_movie in fa_movies:
            alg1 = match.match_algorithm(imdb, current_fa_movie)
            hcmc = match.hard_coded_matches.get(current_fa_movie.movieID)
            alg2 = imdb.match_algorithm_new(current_fa_movie.movieTitle, current_fa_movie.movieYear)
            alg1c = alg1.get_code()
            alg2c = alg2.get_code()

            try:
                if hcmc is None:
                    if alg1c == alg2c:
                        a1hits += 1
                        a2hits += 1
                    else:
                        assert False
                else:
                    assert alg2c == hcmc
                    a2hits += 1
            except:
                raise
            count += 1
            pass
        pass
