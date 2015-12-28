# -*- coding: utf-8 -*-

import faHelper
import sys
from tabulate import tabulate
import codecs
import time
import imdbHelper
import threading, Queue
import re

WORKERS = 4

start_time = time.time() 
logo = '''
`7MM"""YMM  db               `7MMF'`7MMM.     ,MMF'`7MM"""Yb. `7MM"""Yp, 
  MM    `7 ;MM:                MM    MMMb    dPMM    MM    `Yb. MM    Yb 
  MM   d  ,V^MM.     pd*"*b.   MM    M YM   ,M MM    MM     `Mb MM    dP 
  MM""MM ,M  `MM    (O)   j8   MM    M  Mb  M' MM    MM      MM MM"""bg. 
  MM   Y AbmmmqMA       ,;j9   MM    M  YM.P'  MM    MM     ,MP MM    `Y 
  MM    A'     VML   ,-='      MM    M  `YM'   MM    MM    ,dP' MM    ,9 
.JMML..AMA.   .AMMA.Ammmmmmm .JMML..JML. `'  .JMML..JMMmmmdP' .JMMmmmd9                                                                
'''
print(logo)

tLocal= time.localtime()
fa = faHelper.FAhelper()

# Different options to get user ID:
# Option A: You want to write each time User and Password:
sUser = raw_input('Please enter your FilmAffinity USER:')
sPassword = raw_input('Please enter your FilmAffinity PASSWORD:')
fa.setUser(sUser, sPassword)
    
# Option B: You want to hardcode your user and pass 
#    fa.setUser("Your USER", "Your PASSWORD")

# Option C: Hardcode your User ID
# fa.setUserID(123456)
    
fa.login()
if fa.loginSucceed():
    print "Login succeed"
else:
    print "Error on login"
    sys.exit("Not possible to finish task with no login")

print "Your FA ID is: ", fa.getUserID()

# if 0: ONLY for dev

# Download  
fa.getDumpAllVotes()
table = fa.getMoviesDumped()

#     f = open('backup_file.csv', 'r')
#     f.readline()    # pop header line
#     
#     table = []
#     for line in f:
#         movie = line.split(";")
#         table.append(movie)
    
def saveTableToCSV():
    # Save movie list as CSV
    fileName = "FA-movies" + "_" + str(tLocal.tm_year) + "-" + str(tLocal.tm_mon) + "-" + str(tLocal.tm_mday) + ".csv"
    
    file = codecs.open(fileName, "w", "utf_16")
    if len(table[0]) == 9:
        file.write("ID:" + fa.getUserID() + "; Title; Year; Vote; Voted; Country; Director; Cast; Genre\n")
    else:
        file.write("ID fa:" + fa.getUserID() + "; ID imdb; Title; Year; Vote; Voted; Country; Director; Cast; Genre\n")
        
    for movie in table:
        line = ""
        for entry in movie:
            #line = line + entry.encode('utf-8') + ";"
            line = line + entry.replace(";", ",") + ";"
        line = line + "\n"
        file.write(line)
    file.close()
    
    if len(table[0]) == 9:
        # Write table with format
        table_beautiful = tabulate(table, headers=['ID:'+ fa.getUserID(), 'Title', 'Year', 'Vote', 'Voted', 'movieCountry', 'movieDirector', 'movieCast', 'movieGenre'], tablefmt='orgtbl')
    else:
        table_beautiful = tabulate(table, headers=['ID fa: '+ fa.getUserID(), 'ID imdb', 'Title', 'Year', 'Vote', 'Voted', 'movieCountry', 'movieDirector', 'movieCast', 'movieGenre'], tablefmt='orgtbl')
    fileNameBeauty = "FA-moviesBeauty" + "_" + str(tLocal.tm_year) + "-" + str(tLocal.tm_mon) + "-" + str(tLocal.tm_mday) + ".txt"
    fileBeauty = codecs.open(fileNameBeauty, "w", "utf_16")
    fileBeauty.write(table_beautiful)
    fileBeauty.close()

def getImdbIdsThread(queue):
    while True:
        index = queue.get()
        if index is None:
            queue.task_done() 
            break
        imdbID = imdb.getMovieCodeByAPI(table[index][1], table[index][2])
        if imdbID[0] == "bm0000000":
            imdbID = imdb.getMovieCode(table[index][1], table[index][2])
        if imdbID[0] == "bm0000000":
            t = re.sub('\([\w\W]*?\)', '', table[index][1]).strip()
            imdbID = imdb.getMovieCode(t, table[index][2])
        if imdbID[0] == "bm0000000" or imdbID[0] == None:
            imdbNotFound.append([table[index][0], table[index][1], table[index][2]])
        print "[Match IMDB] tt" + table[index][0], "is: ", table[index][1], " (" + table[index][2] + ")"
        table[index] = [table[index][0],imdbID[0].decode(), table[index][1], table[index][2], table[index][3], table[index][4], table[index][5], table[index][6], table[index][7], table[index][8]]
        if index % 10 == 0:
            print "Task progress: " + str(index) + "/" + str(len(table)) + " (" + str(index*100/float(len(table)))[:5] + "%)" 
        queue.task_done()    

def voteImdbThread(queue):
    while True:
        index = queue.get()
        if index is None:
            queue.task_done() 
            break
        try:
            if table[index][1] != "bm0000000":
                imdb.voteMovie(table[index][1], table[index][4])
        except:
            e = sys.exc_info()
            imdbNotVoted.append([table[index][0], table[index][1], table[index][2]])
            print "ERROR: en pelicula", table[index][1], table[index][2]
        if index % 10 == 0:
            print "Task progress: " + str(index) + "/" + str(len(table)) + " (" + str(index*100/float(len(table)))[:5] + "%)"
        queue.task_done()  

sIn = raw_input('\r\nDo you want to backup to IMDB? <Y> or <N>:')
while (sIn.lower()!="y" and sIn.lower()!="n"):
    sIn = raw_input('Do you want to backup to IMDB? <Y> or <N>:')
if sIn.lower() == "y":
    imdb = imdbHelper.IMDBhelper()

    # Cola con las pelis para obterner el codigo de pelicula en IMDB    
    q = Queue.Queue()
    # Array para las peliculas que presenten peliculas
    imdbNotFound = []
    imdbNotVoted = []
    
    # Start multi-thread. One thread for each worker, all use same queue.
    threads = []
    for i in range(WORKERS):
        worker = threading.Thread(target=getImdbIdsThread, args=(q,))
        worker.setDaemon(True)
        worker.start()
        threads.append(worker)
    
    # Enqueue all movies in queue
    for i in range(len(table)):
        q.put(i)
    
    for i in range(WORKERS):
        q.put(None) # add end-of-queue markers
        
    # Wait threads and workers to finish
    q.join()
    
    if len(imdbNotFound) > 0:
        print "\r\nCaution: ", len(imdbNotFound), " FA movies could not be fount in IMDB!"
        # Write table with format
        table_notFound = tabulate(imdbNotFound, headers=['ID fa: '+ fa.getUserID(), 'ID imdb', 'Title', 'Year', 'Vote', 'Voted', 'movieCountry', 'movieDirector', 'movieCast', 'movieGenre'], tablefmt='orgtbl')
        fileNameNotFound = "FilmsNotFoundAtIMDB" + "_" + str(tLocal.tm_year) + "-" + str(tLocal.tm_mon) + "-" + str(tLocal.tm_mday) + ".txt"
        fileNotFound = codecs.open(fileNameNotFound, "w", "utf_16")
        fileNotFound.write(table_notFound)
        fileNotFound.close()
        print "Movies not found:"
        print table_notFound 

    print "\r\nAll movies from FA matched with IMDB database.\r\n"
    print("--- Total runtime %s seconds ---" % (time.time() - start_time))
    

    # Option A: You want to write each time User and Password:
    sUser = raw_input('Please enter your FilmAffinity USER:')
    sPassword = raw_input('Please enter your FilmAffinity PASSWORD:')
    imdb.setUser(sUser, sPassword)
    
    # Option B: You want to hardcode your user and pass
    # imdb.setUser("user@gmail.com", "imdb_pass")
    
    # Login to IMDB
    imdb.login()
    while not imdb.loginSucceed():
        imdb.login()
    print "Login succeed"
    qVotes = Queue.Queue(maxsize=0)
    
    for i in range(WORKERS):
        voter = threading.Thread(target=voteImdbThread, args=(qVotes,))
        voter.setDaemon(True)
        voter.start()
    
    for i in range(len(table)):
        qVotes.put(i)
    
    for i in range(WORKERS):
        q.put(None) # add end-of-queue markers
    
    qVotes.join()
        
    if len(imdbNotVoted)>0:
        print "\r\nCaution: It was not possible to vote ", len(imdbNotVoted), " movies"
        # Write table with format
        table_notVoted = tabulate(imdbNotVoted, headers=['ID fa: '+ fa.getUserID(), 'ID imdb', 'Title', 'Year', 'Vote', 'Voted', 'movieCountry', 'movieDirector', 'movieCast', 'movieGenre'], tablefmt='orgtbl')
        fileNameNotFound = "FilmsNotVotedAtIMDB" + "_" + str(tLocal.tm_year) + "-" + str(tLocal.tm_mon) + "-" + str(tLocal.tm_mday) + ".txt"
        fileNotFound = codecs.open(fileNameNotFound, "w", "utf_16")
        fileNotFound.write(imdbNotVoted)
        fileNotFound.close()
        print "Movies not found:"
        print smart_str(table_notFound) 
    
saveTableToCSV()

print("--- Total runtime %s seconds ---" % (time.time() - start_time))
print "\r\nDONE"
