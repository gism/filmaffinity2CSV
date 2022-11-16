import glob
import os
import csv
from datetime import datetime
import time
import sys


# Script to generate statistics report
# input is .csv file
# if there is no input script will search for latest .csv on the folder

def count_array_reps(a):
    dict_a = {i: a.count(i) for i in a}
    sort_dic_a = dict(sorted(dict_a.items()))
    return sort_dic_a


def ascii_bar_chart(dic):
    s = ""

    max_value = max(count for _, count in dic)
    increment = max_value / 25

    longest_label_length = max(len(label) for label, _ in dic)

    total_sum = 0
    for d in dic:
        total_sum = total_sum + d[1]

    for label, count in dic:

        # The ASCII block elements come in chunks of 8, so we work out how
        # many fractions of 8 we need.
        # https://en.wikipedia.org/wiki/Block_Elements
        bar_chunks, remainder = divmod(int(count * 8 / increment), 8)

        # First draw the full width chunks
        bar = '█' * bar_chunks

        # Then add the fractional part.  The Unicode code points for
        # block elements are (8/8), (7/8), (6/8), ... , so we need to
        # work backwards.
        if remainder > 0:
            bar += chr(ord('█') + (8 - remainder))

        # If the bar is empty, add a left one-eighth block
        bar = bar or '▏'

        percentage = (count / total_sum) * 100;

        s = s + f'{label.rjust(longest_label_length)} ▏ {count:#4d} | {percentage:4.1f}%  {bar}' + "\n"

    return s


def ascii_bar_chart_2(dic, dic_rates):
    s = ""

    max_value = max(count for _, count in dic)
    increment = max_value / 25

    longest_label_length = max(len(label) for label, _ in dic)

    total_sum = 0
    for d in dic:
        total_sum = total_sum + d[1]

    for label, count in dic:

        # The ASCII block elements come in chunks of 8, so we work out how
        # many fractions of 8 we need.
        # https://en.wikipedia.org/wiki/Block_Elements
        bar_chunks, remainder = divmod(int(count * 8 / increment), 8)

        # First draw the full width chunks
        bar = '█' * bar_chunks

        # Then add the fractional part.  The Unicode code points for
        # block elements are (8/8), (7/8), (6/8), ... , so we need to
        # work backwards.
        if remainder > 0:
            bar += chr(ord('█') + (8 - remainder))

        # If the bar is empty, add a left one-eighth block
        bar = bar or '▏'

        percentage = (count / total_sum) * 100;

        rate_avg = dic_rates[label][2]

        bar_chunks_rates, remainder_rates = divmod(int(rate_avg * 8 * 40 / 10), 8)
        bar_rates = '█' * bar_chunks_rates
        if remainder_rates > 0:
            bar_rates += chr(ord('█') + (8 - remainder_rates))
        bar_rates = bar_rates or '▏'

        s = s + f'{label.rjust(longest_label_length)} ▏ {count:#4d} | {percentage:4.1f}%  {bar.ljust(25)}  |  {rate_avg:5.1f}  {bar_rates.ljust(25)}' + "\n"

    return s


def num_to_month(s):
    if s == '01':
        return 'Jan'
    elif s == '02':
        return 'Feb'
    elif s == '03':
        return 'Mar'
    elif s == '04':
        return 'Abr'
    elif s == '05':
        return 'May'
    elif s == '06':
        return 'Jun'
    elif s == '07':
        return 'Jul'
    elif s == '08':
        return 'Aug'
    elif s == '09':
        return 'Sep'
    elif s == '10':
        return 'Oct'
    elif s == '11':
        return 'Nov'
    elif s == '12':
        return 'Dec'
    else:
        return '???'


def search_newest_csv_file():

    list_of_files = glob.glob('*.csv')
    latest_file = max(list_of_files, key=os.path.getctime)

    return latest_file


def generate_stats_report(csv_file_path):

    print("Generating report. It may take some seconds.")

    with open(csv_file_path, encoding='utf-16') as data_file:
        line = data_file.readline()
        print(line)
        reader = csv.reader(data_file, delimiter=';', lineterminator='\n')
        movie_array = list(reader)

    years_array = []
    vote_array = []
    voted_array = []
    country_array = []
    genre_array = []
    for movie in movie_array:
        years_array.append(movie[2])
        vote_array.append(movie[3])
        voted_array.append(movie[4])
        country_array.append(movie[7])
        genre_array.append(movie[10])

    total_movies = len(movie_array)
    # print("Total Movies: " + str(total_movies))

    vote_array = count_array_reps(vote_array)  # Sort Vote Array Asc
    # print(vote_array)

    years_array = count_array_reps(years_array)  # Sort Year Array Asc
    # print(years_array)

    country_array = count_array_reps(country_array)  # Sort Country Array Asc Alphabetical
    country_array = dict(
        sorted(country_array.items(), key=lambda item: item[1], reverse=True))  # Descending order (from value)
    # print(country_array)

    voted_array_month = []
    for vote in voted_array:
        voted_array_month.append(vote[:-2])
    # print(voted_array_month)

    voted_array_month = count_array_reps(voted_array_month)

    first_vote = list(voted_array_month.keys())[0]
    first_vote_year = int(first_vote[:4])
    first_vote_month = int(first_vote[4:])

    current_year = datetime.now().year
    current_month = datetime.now().month

    year = first_vote_year
    while year <= current_year:
        for m in range(1, 13):
            if m < 10:
                m2 = "0" + str(m)
            else:
                m2 = str(m)

            k = str(year) + m2

            if k not in voted_array_month:
                if year == int(first_vote_year) and m < int(first_vote_month):
                    continue
                if year == current_year and m > current_month:
                    continue
                # print("Month with no votes: " + k)
                voted_array_month[k] = 0
        year = year + 1

    voted_array_month = {key: value for key, value in sorted(voted_array_month.items())}
    # print(voted_array_month)

    maingenre_array = []
    subgenre_array = []
    for g in genre_array:
        g = g.split("|")

        main_g = g[0]

        if len(g) > 1:
            sub_g = g[1]
        else:
            sub_g = ""

        main_g = main_g.split(".")
        sub_g = sub_g.split(".")

        for mg in main_g:
            maingenre_array.append(mg.strip())
        for sg in sub_g:
            subgenre_array.append(sg.strip())

    maingenre_array = count_array_reps(maingenre_array)  # Sort Main Genre Array Asc Alphabetical
    maingenre_array = dict(
        sorted(maingenre_array.items(), key=lambda item: item[1], reverse=True))  # Descending order (from value)
    # print(maingenre_array)

    subgenre_array = count_array_reps(subgenre_array)  # Sort Main Genre Array Asc Alphabetical
    subgenre_array = dict(
        sorted(subgenre_array.items(), key=lambda item: item[1], reverse=True))  # Descending order (from value)
    # print(subgenre_array)

    # Get rates for each year
    years_array_rates = {}
    for y in years_array:
        year_sum = 0
        year_movies = 0
        for m in movie_array:
            if int(m[2]) == int(y):
                year_sum = year_sum + int(m[3])
                year_movies = year_movies + 1
        year_entry = (y, year_movies, year_sum / year_movies)
        years_array_rates[y] = year_entry
    # print(years_array_rates)

    # Get rates for each Country
    country_array_rates = {}
    for c in country_array:
        country_sum = 0
        country_movies = 0
        for m in movie_array:
            if m[7] == c:
                country_sum = country_sum + int(m[3])
                country_movies = country_movies + 1
        country_entry = (c, country_movies, country_sum / country_movies)
        country_array_rates[c] = country_entry
    # print(country_array_rates)

    maingenre_array_rates = {}
    for g in maingenre_array:
        genre_sum = 0
        genre_movies = 0
        for m in movie_array:
            mg = m[10].split("|")
            mg = mg[0]
            if g in mg:
                genre_sum = genre_sum + int(m[3])
                genre_movies = genre_movies + 1
        genre_entry = (g, genre_movies, genre_sum / genre_movies)
        maingenre_array_rates[g] = genre_entry
    # print(maingenre_array_rates)

    subgenre_array_rates = {}
    for g in subgenre_array:
        sub_genre_sum = 0
        sub_genre_movies = 0
        for m in movie_array:
            mg = m[10].split("|")
            if len(mg) > 1:
                sub_g = mg[1]
            else:
                continue

            if g in sub_g:
                sub_genre_sum = sub_genre_sum + int(m[3])
                sub_genre_movies = sub_genre_movies + 1
        sub_genre_entry = (g, sub_genre_movies, sub_genre_sum / sub_genre_movies)
        subgenre_array_rates[g] = sub_genre_entry
    # print(subgenre_array_rates)

    voted_array_month_rates = {}
    for d in voted_array_month:
        month_sum = 0
        month_movies = 0
        for m in movie_array:
            if d in m[4][:-2]:
                month_sum = month_sum + int(m[3])
                month_movies = month_movies + 1
        d = d[:-2] + '-' + num_to_month(d[4:])
        if month_movies == 0:
            month_entry = (d, month_movies, 0)
        else:
            month_entry = (d, month_movies, month_sum / month_movies)
        voted_array_month_rates[d] = month_entry
    # print(voted_array_month_rates)

    # Prepare Arrays:
    vote_array_iterable = []
    vote_array['10'] = vote_array.pop('10')
    vote_array = dict(list(vote_array.items())[::-1])
    for v in vote_array:
        vote_array_iterable.append((v, vote_array[v]))
    # print(vote_array_iterable)

    year_array_iterable = []
    for y in years_array:
        year_array_iterable.append((y, years_array[y]))
    # print(year_array_iterable)

    country_array_iterable = []
    for c in country_array:
        country_array_iterable.append((c, country_array[c]))
    # print(country_array_iterable)

    maingenre_array_iterable = []
    for g in maingenre_array:
        maingenre_array_iterable.append((g, maingenre_array[g]))
    # print(maingenre_array_iterable)

    subgenre_array_iterable = []
    for g in subgenre_array:
        if g == '':
            continue
        subgenre_array_iterable.append((g, subgenre_array[g]))
    # print(subgenre_array_iterable)

    voted_array_month_iterable = []
    for v in voted_array_month:
        v2 = v[:-2] + '-' + num_to_month(v[4:])
        voted_array_month_iterable.append((v2, voted_array_month[v]))
    # print(voted_array_month_iterable)

    report_file_name = csv_file_path[:-4] + "_STATS.txt"
    print("Report file: ", report_file_name)
    reportFile = open(report_file_name, "w", encoding="utf-8")

    file = csv_file_path
    reportFile.write("FilmAffinity2CSV_Stats_Report from: " + file + "\n")

    date_time_obj = datetime.now()
    timestamp_str = date_time_obj.strftime("%d-%b-%Y (%H:%M:%S.%f)")
    reportFile.write("At: " + timestamp_str + "\n")

    reportFile.write("\nTotal Movies: " + str(total_movies) + "\n")

    vote_bar_chart = ascii_bar_chart(vote_array_iterable)
    reportFile.write("\nRatings by valuation:\n")
    reportFile.write(vote_bar_chart + "\n")

    # year_bar_chart = ascii_bar_chart(year_array_iterable)
    year_bar_chart = ascii_bar_chart_2(year_array_iterable, years_array_rates)
    reportFile.write("Ratings by year:\n")
    reportFile.write(year_bar_chart + "\n")

    # country_bar_chart = ascii_bar_chart(country_array_iterable)
    country_bar_chart = ascii_bar_chart_2(country_array_iterable, country_array_rates)
    reportFile.write("Ratings by country:\n")
    reportFile.write(country_bar_chart + "\n")

    # main_genre_bar_chart = ascii_bar_chart(maingenre_array_iterable)
    main_genre_bar_chart = ascii_bar_chart_2(maingenre_array_iterable, maingenre_array_rates)
    reportFile.write("Ratings by genre:\n")
    reportFile.write(main_genre_bar_chart + "\n")

    # sub_genre_bar_chart = ascii_bar_chart(subgenre_array_iterable)
    sub_genre_bar_chart = ascii_bar_chart_2(subgenre_array_iterable, subgenre_array_rates)
    reportFile.write("Ratings by sub-genre:\n")
    reportFile.write(sub_genre_bar_chart + "\n")

    # voted_array_month_bar_chart = ascii_bar_chart(voted_array_month_iterable)
    voted_array_month_bar_chart = ascii_bar_chart_2(voted_array_month_iterable, voted_array_month_rates)
    reportFile.write("Rating history:\n")
    reportFile.write(voted_array_month_bar_chart + "\n")

    reportFile.close()


if __name__ == "__main__":

    start_time = time.time()

    if len(sys.argv) > 1:

        input_file = sys.argv[1]                # use first argument to indicate input csv file

        if os.path.exists(input_file):
            generate_stats_report(input_file)

        else:
            print("ERROR! Input file not found: " + input_file)

    else:
        last_csv = search_newest_csv_file()

        if last_csv is None:
            print("ERROR NO CSV FOUND!")
            sys.exit()

        print("Newest CSV found: " + last_csv)
        generate_stats_report(last_csv)

    print(("--- Total runtime %s seconds ---" % (time.time() - start_time)))
    print("DONE")

