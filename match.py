import faHelper

hard_coded_matches = {'809297': 'tt0068646', '573847': 'tt0276919', '509573': 'tt0970416'}


def match_algorithm(imdb, current_fa_movie):
    assert isinstance(current_fa_movie, faHelper.FAhelper.FAMovieData)
    fa_id = current_fa_movie.get_id()
    if fa_id == '809297':
        pass
    imdbID = imdb.match_alg_2(current_fa_movie.get_title(), current_fa_movie.get_year())

    use_hard_coded_matches = True
    if use_hard_coded_matches:
        if fa_id in hard_coded_matches:
            imdbID = imdb.get_from_code(hard_coded_matches[fa_id])
    return imdbID
