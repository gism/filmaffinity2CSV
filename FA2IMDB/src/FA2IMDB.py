import webThreadFA
import webThreadIMDB
import time
import sys
import os, inspect

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

# If you already got the CSV file and you want to upload to IMDB.
# Movie title; Year; Director; Vote; Movie ID
def getDataCSV(filename):
    
    fin=open(filename, 'r')
    allCSV = fin.read()
    fin.close
    
    print("Reading CSV information")
    
    FAdata=[]
    
    # One line one movie info.
    # One movie info, 5 movie fields.
    lines = allCSV.split("\n")
    for line in lines:
        entries = line.split(";")
        FAdata.append(entries)
        
        # print("+-----------------------------+")
        # print(line)
    
    print("Number of movies in the CSV: " + str(len(FAdata)))
    print("")
    return FAdata

# Filmaffinity or IMDB:
sMenu = '''Type:
1: To save your Filmaffinity vote information to CSV file.
2: To save your Filmaffnity vote information to CSV fie and vote it in IMDB website.
3: To vote you Filmaffinity information in IMDB website.
4: To save you IMDB vote information to CSV file.
5: To vote a CSV file to IMDB.
6: Close.

Option: '''

sIn = raw_input(sMenu)
while (not sIn or not sIn.isdigit() or int(sIn)>6 or int(sIn)<1):
    print("")
    sIn = raw_input(sMenu)

print("")

oAllData=[]

sIn= int(sIn)
if sIn == 1:
    
    outFolder = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "\data" + chr(92)
    tLocal= time.localtime()
    sFilename = outFolder + "FA-Votes_" + "_" + str(tLocal.tm_year) + "-" + str(tLocal.tm_mon) + "-" + str(tLocal.tm_mday) + ".csv"
    sIn = raw_input('Default file name is:\n' + sFilename + "\nDo you want to change it? <Y> or <N>:\n")
    
    while (sIn.lower()!="y" and sIn.lower()!="n"):
        sIn = raw_input('Default file name is:\n' + sFilename + "\nDo you want to change it? <Y> or <N>:\n")
        
    if sIn.lower() == "y":
        sFilename = raw_input('Enter a valid path + filename:')
    else:
        if not os.path.exists(outFolder):
            os.makedirs(outFolder)
        
    oAllData = webThreadFA.getDataFA(sFilename, oAllData)

elif sIn ==2:
    
    outFolder = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "\data" + chr(92)
    tLocal= time.localtime()
    sFilename = outFolder + "FA2IMDB-Votes_" + "_" + str(tLocal.tm_year) + "-" + str(tLocal.tm_mon) + "-" + str(tLocal.tm_mday) + ".csv"
    
    sIn = raw_input('Default file name is:\n' + sFilename + "\nDo you want to change it? <Y> or <N>:\n")
    while (sIn.lower()!="y" and sIn.lower()!="n"):
        sIn = raw_input('Default file name is:\n' + sFilename + "\nDo you want to change it? <Y> or <N>:\n")
    
    if sIn.lower() == "y":
        sFilename = raw_input('Enter a valid path + filename:')
    else:
        if not os.path.exists(outFolder):
            os.makedirs(outFolder)
            
    sFileTemp = outFolder + "deleteme_please.tmp"
    oAllData = webThreadFA.getDataFA(sFileTemp, oAllData)
    os.remove(sFileTemp)
    
    webThreadIMDB.postData(oAllData, sFilename)
                               
elif sIn ==3:
    sFileTemp = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "deleteme_please.tmp"
    oAllData = webThreadFA.getDataFA(sFileTemp, oAllData)
    os.remove(sFileTemp)
    webThreadIMDB.postData(oAllData, sFileTemp)
    os.remove(sFileTemp)

elif sIn ==4:
    
    outFolder = sys.path[0] + "\data" + chr(92)
    tLocal= time.localtime()
    sFilename = outFolder + "IMDB-Votes_" + "_" + str(tLocal.tm_year) + "-" + str(tLocal.tm_mon) + "-" + str(tLocal.tm_mday) + ".csv"
    sIn = raw_input('Default file name is:\n' + sFilename + "\nDo you want to change it? <Y> or <N>:\n")
    
    while (sIn.lower()!="y" and sIn.lower()!="n"):
        sIn = raw_input('Default file name is:\n' + sFilename + "\nDo you want to change it? <Y> or <N>:\n")
    
    if sIn.lower() == "y":
        sFilename = raw_input('Enter a valid path + filename:')
    else:
        if not os.path.exists(outFolder):
            os.makedirs(outFolder)
    
    webThreadIMDB.getData(oAllData, sFilename)
elif sIn == 5:
    
    # Change the filename. That one was for testing.
    sFilename = 'C:\FA-Votes__2013-8-16.csv'
    oAllData = getDataCSV(sFilename)
    sFilename = 'C:\FA-Votes__2013-8-16_imdb.csv'
    webThreadIMDB.postData(oAllData, sFilename)
    
else:
    pass

#Bye-Bye
print ("See you.")