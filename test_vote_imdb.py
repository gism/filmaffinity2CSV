import imdbHelper
import faHelper
import sys
import os
import time
import stat

import config

path = "./"
files_sorted_by_date = []

filepaths = [os.path.join(path, file) for file in os.listdir(path)]

file_statuses = [(os.stat(filepath), filepath) for filepath in filepaths]

files = ((status[stat.ST_CTIME], filepath) for status, filepath in file_statuses if stat.S_ISREG(status[stat.ST_MODE]))

first_csv = None

for creation_time, filepath in sorted(files):
    creation_date = time.ctime(creation_time)
    filename = os.path.basename(filepath)
    name, file_extension = os.path.splitext(filename)

    if file_extension == '.csv':
        last_csv = filename

    files_sorted_by_date.append(creation_date + " " + filename + file_extension)

if last_csv is None:
    print("ERROR NO CSV FOUND!")
    sys.exit()

print("Lastest CSV found: " + last_csv)

f = open(last_csv, "r")
f.readline()

fa_csv_movies = []

for line in f:
    # TODO: Check where \x00 comes from!
    line = line.replace('\x00', '')

    movie = line.split(';')
    if len(movie) > 12:
        fa_movie = faHelper.FAMovieData(movie_id=movie[0], movie_title=movie[1], movie_year=movie[2],
                                        movie_rate=movie[3], vote_day_yyyymmdd=movie[4])

        fa_movie.set_movie_details(movie_fa_rate=movie[5], movie_fa_votes=movie[6],
                                   movie_country=movie[7], movie_director=movie[8], movie_cast=movie[9],
                                   movie_genre=movie[10], movie_duration=movie[11], movie_synopsis=movie[12])

        fa_csv_movies.append(fa_movie)

imdb = imdbHelper.ImdbHelper()
imdb.set_user(config.u_imdb, config.p_imdb)

movies_with_imdb_codes = []

for movie in fa_csv_movies:
    # print("Looking for: " + movie.get_title() + " (" + movie.get_year() + ")")
    m = imdb.search_movie_id(movie.get_title(), movie.get_year())
    if m.get_id() is None:
        print("ERROR: Movie not found: " + movie.get_title() + " (" + movie.get_year() + ")")
    else:
        print("Found: " + m.get_id() + " - " + movie.get_title() + " (" + movie.get_year() + ")")
        movies_with_imdb_codes.append([movie, m])

# Save file with all FA information
list_movies = imdbHelper.FAMovieExtraList()

# movies_with_imdb_codes does not include Not found movies!
for movie_match in movies_with_imdb_codes:

    fa_movie = movie_match[0]
    imdb_movie = movie_match[1]

    new_movie = imdbHelper.FAMovieDataExtra(fa_movie.get_id(),
                                            fa_movie.get_title(),
                                            fa_movie.get_year(),
                                            fa_movie.get_rate(),
                                            fa_movie.get_rate_day_yyyymmdd())

    new_movie.set_movie_details(fa_movie.get_fa_rate(),
                                fa_movie.get_fa_votes(),
                                fa_movie.get_country(),
                                fa_movie.get_director(),
                                fa_movie.get_cast(),
                                fa_movie.get_genre(),
                                fa_movie.get_duration(),
                                fa_movie.get_synopsis())

    new_movie.set_imdb_details(imdb_movie.get_id(), imdb_movie.get_title(), imdb_movie.get_year())

    list_movies.append(new_movie)


imdb.do_login()
print("IMDB login result: " + str(imdb.login_succeed()))

for m in list_movies.get_movies():

    current_imdb_vote = imdb.get_movie_vote(m.get_imdb_id())
    print("Movie: " + m.get_imdb_id() + " FA rate: " + str(m.get_rate()) + " IMDB rate: " + str(current_imdb_vote))

    fa_rate = m.get_rate().replace('\x00', '')
    if int(current_imdb_vote) != int(fa_rate):
        imdb.vote_movie(m.get_imdb_id(), fa_rate)
        print("Voted: " + m.get_imdb_id() + " (" + m.get_title() + " - " + m.get_year() + ") Rate: " + fa_rate)

print('')

t_local = time.localtime()

csv_file_name = "imdb_" + last_csv
list_movies.save_csv(csv_file_name)
print(("IMDB movie list (CSV) saved at: " + csv_file_name))

table_file_name = "IMDB_" + last_csv + ".txt"
table_ascii = list_movies.save_report(table_file_name)
print(("IMDB movie table (TXT) saved at: " + table_file_name))

print('')

print(table_ascii)
