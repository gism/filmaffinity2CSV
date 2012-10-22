import webThreadFA
import webThreadIMDB
import time

# Folder to put information.
outFolder="C:\\"
sFilename=""
oAllData=[]

def getDataCSV(outFile):
	
	fin=open(outFile, 'r')
	allCSV = fin.readlines()
	fin.close
	
	# One line one movie info. 
	for lines in allCSV:
		entries = lines.split("\r")
		
	# One movie info, 5 movie fields.
	FAdata=[]
	for movies in entries:
		movie = movies.split(";")
		FAdata.append(movie)
	FAdata.pop(len(FAdata)-1)	
	return FAdata
	
# Get personal votes from FA website:
sIn = raw_input('Do you want to dump your FilmAffinity data? <Y> or <N>:')
while (sIn.lower()!="y" and sIn.lower()!="n"):
	sIn = raw_input('Do you want to dump your FilmAffinity data? <Y> or <N>:')
if sIn.lower() == "y":
	tLocal= time.localtime()
	sFilename = outFolder + "FA-Votes_" + "_" + str(tLocal.tm_year) + "-" + str(tLocal.tm_mon) + "-" + str(tLocal.tm_mday) + ".csv"

	oAllData = webThreadFA.getDataFA(sFilename, oAllData)


sDumbedFile = "C:\\FA-Votes__2012-10-16.csv"
oAllData = getDataCSV(sDumbedFile)


# Post personal votes in IMDB website:
sIn = raw_input('Do you want to vote read data in IMDB? <Y> or <N>:')
while (sIn.lower()!="y" and sIn.lower()!="n"):
	sIn = raw_input('Do you want to vote read data in IMDB? <Y> or <N>:')
if sIn.lower() == "y":
	sIn = raw_input('Save it to CSV file? <Y>, <N> or <F>:')
	while (sIn.lower()!="y" and sIn.lower()!="n" and sIn.lower()!="f"):
		sIn = raw_input('Save it to CSV file? <Y>, <N> or <F>:')
	if sIn.lower() == "y":
		tLocal= time.localtime()
		sFilename = outFolder + "FA2IMDB-Votes_" + "_" + str(tLocal.tm_year) + "-" + str(tLocal.tm_mon) + "-" + str(tLocal.tm_mday) + ".csv"
		print("Export data file: "+ sFilename)
	elif sIn.lower() == "f":			
		sIn = raw_input('Write path + filename + extension:')
		sFilename = sIn
		print("Export data file: "+ sFilename)
	else:
		sFilename = ""
	webThreadIMDB.postData(oAllData, sFilename)

# Get personal votes from IMDB website:
sIn = raw_input('Do you want to dump your IMDB data? <Y> or <N>:')
while (sIn.lower()!="y" and sIn.lower()!="n"):
	sIn = raw_input('Do you want to dump your IMDB data? <Y> or <N>:')
if sIn.lower() == "y":
	sIn = raw_input('Save it to CSV file? <Y>, <N> or <F>:')
	while (sIn.lower()!="y" and sIn.lower()!="n" and sIn.lower()!="f"):
		sIn = raw_input('Save it to CSV file? <Y>, <N> or <F>:')
	if sIn.lower() == "y":
		tLocal= time.localtime()
		sFilename = outFolder + "IMDB-Votes_" + "_" + str(tLocal.tm_year) + "-" + str(tLocal.tm_mon) + "-" + str(tLocal.tm_mday) + ".csv"
		print("Export data file: "+ sFilename)
	elif sIn.lower() == "f":			
		sIn = raw_input('Write path + filename + extension:')
		sFilename = sIn
		print("Export data file: "+ sFilename)
	else:
		sFilename = ""
	webThreadIMDB.getData(oAllData, sFilename)

#Bye-Bye
print ("End of program. See you.")