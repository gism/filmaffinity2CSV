# -*- coding: utf-8 -*-

import time
import sys

import faHelper


def main_fa_2_csv():
    start_time = time.time()
    logo = '''                                                         
        `7MM"""YMM  db                 .g8"""bgd  .M"""bgd `7MMF'   `7MF'
          MM    `7 ;MM:              .dP'     `M ,MI    "Y   `MA     ,V  
          MM   d  ,V^MM.     pd*"*b. dM'       ` `MMb.        VM:   ,V   
          MM""MM ,M  `MM    (O)   j8 MM            `YMMNq.     MM.  M'   
          MM   Y AbmmmqMA       ,;j9 MM.         .     `MM     `MM A'    
          MM    A'     VML   ,-='    `Mb.     ,' Mb     dM      :MM;     
        .JMML..AMA.   .AMMA.Ammmmmmm   `"bmmmd'  P"Ybmmd"        VF 
    '''
    print(logo)

    # Check if driver for robot solver is present (only warning)
    faHelper.FAhelper.check_robot_solver_requirements()

    # Create a FilmAfinity handler
    fa = faHelper.FAhelper()

    user_id = ""
    user_name = ""
    user_password = ""

    try:
        # Configuration file is not mandatory (just to avoid introducing credentials each run)
        import config
        user_name = config.fauser
        user_password = config.fapass
        user_id = config.fauser_id

    except:
        print("ERROR: No config.py found")

    if user_id == "" or (not user_id.isdigit()):
        fa.set_user(user_name, user_password)
        fa.login()
        if fa.login_succeed():
            print("Login succeed")
        else:
            print("Error on login")
            sys.exit("Not possible to finish task with no login")
        print(("Your FA ID is: ", fa.get_user_id()))
    else:
        fa.set_user_id(user_id)

    fa.get_dump_all_votes()
    fa_movies = fa.get_movies_dumped()

    # Save file with all FA information
    list_fa_movies = faHelper.FAMovieList()
    for movie in fa_movies:
        list_fa_movies.append(movie)

    t_local = time.localtime()

    print('')

    csv_file_name = "FA_" + str(t_local.tm_year) + "_" + str(t_local.tm_mon) + "_" + str(
        t_local.tm_mday) + '_fauser' + fa.get_user_id() + ".csv"
    list_fa_movies.save_csv(csv_file_name)
    print(("FilmAffinity movie list (CSV) saved at: " + csv_file_name))

    table_file_name = "FA_" + str(t_local.tm_year) + "_" + str(t_local.tm_mon) + "_" + str(
        t_local.tm_mday) + '_fauser' + fa.get_user_id() + ".txt"
    table_ascii = list_fa_movies.save_report(table_file_name)
    print(("FilmAffinity movie table (TXT) saved at: " + table_file_name))

    print('')

    print(table_ascii)

    print(("--- Total runtime %s seconds ---" % (time.time() - start_time)))
    print("\r\nDONE")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main_fa_2_csv()
