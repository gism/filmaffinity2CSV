import threading, Queue
import sys
import re
import xml.sax.saxutils as saxutils
import cookielib, urllib, urllib2
import time

# FA URL set.
urlLogin= "http://www.filmaffinity.com/en/login.php"
urlVotes = "http://www.filmaffinity.com/en/myvotes.php"
urlVotes_prefix = "http://www.filmaffinity.com/en/myvotes.php?p="
urlVotes_sufix = "&orderby="

outOrder_votacion = "0"
outOder_year = "1"
outOrder_title = "2"
outOrder_director = "3"
outOrder_voteDate = "4"


# Put your account information here.
# Or define bAskUser = False if you want to write it each time you run the code.
def getUser():
    
    #bAskUser = False
    bAskUser = True    
        
    if bAskUser:
        sUser = raw_input('Please enter your FilmAffinity USER:')
        sPassword = raw_input('Please enter your FilmAffinity PASSWORD:')
        return sUser, sPassword    
    else:
        return "YourUserHERE" , "YourPasswordHERE"

# App virtual login to Filmaffinity.
def login():
    
    user, password = getUser()
    
    # Enable cookie support for urllib2
    cookiejar = cookielib.CookieJar()
    webSession = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))

    webSession.open(urlLogin)
    
    # Post data to Filmaffinity login URL.
    dataForm =  {"postback": 1, "rp": "", "user":user, "password":password}
    dataPost = urllib.urlencode(dataForm)

    request = urllib2.Request(urlLogin, dataPost)
    webSession.open(request)  # Our cookiejar automatically receives the cookies, after the request
    
    # Return the cookies and the session authorization. 
    return webSession, cookiejar

# This function return the number of pages to scan and the number of voted movies.
# Parameters: URL of the user list and the web session.
# It's not needed to make login, because you can see anyone votes database, but It is funnier :D 
def getNumberPagesFA(url, webSession):
    
    webResponse = webSession.open(url)
    
    # Just use the regular expression to find the data.
    # /!\ If FA web changes you must change this regular expression.
    pattern = re.compile ('Page number <b>1<\/b> of <b>([\d]+)<\/b>[\w\W\s\S]+Number of movies rated: <b>([\d]+)<\/b><\/td><\/tr>')    # Pattern ENGLISH.v1 MUCH BETTER!
    match = pattern.search (webResponse.read())
    
    numPages = match.group(1)
    numVotes = match.group(2)
    
    return numPages, numVotes

# Main function to launch to get all Filmaffinity data.
def getDataFA(sFilename, oAllData):
    
    global urlVotes    
    
    # Login to Filmaffinity. Not needed if you already know your user ID.
    webSession, cookiejar = login()
    if len(cookiejar) < 2:
        print ("Login error!: Incorrect FA User or password, please try again.")
        return -1, -1

    # Getting number of pages and movies rated in FA.
    numPages, numVotes = getNumberPagesFA(urlVotes, webSession)
    print ("Looking for {0} movies in {1} pages." .format (numVotes,numPages))
    
    # Open or create a file to put all dumped data.
    if sFilename != "":
        if not printFile(sFilename, ""):
            print("Critical ERROR! Impossible to open: " + sFilename)
            return -1
    
    # At this point we should launch multiple threats to get all votes from different pages.
    t=[]
    i=1
    queueFA=Queue.Queue()
    
    # Queue for the output file. We want to avoid collisions and loss of data.
    fileWrite = ThreadFileAdd(sFilename, queueFA)
    if sFilename != "":
        fileWrite.start()
    
    # Scan all pages from users vote list looking for the data.
    while i<=int(numPages):
    
        print ("Requesting page: " + str(i) + " from FA website.")
        urlVotes= urlVotes_prefix + str(i) + urlVotes_sufix + outOrder_title
        
        # Enqueue requests. 
        t.append(ThreadGet(urlVotes, webSession, i, queueFA, oAllData))
        t[i-1].start()
        i+=1
        
        # Arbitrary value, just to avoid launching hundeds of request at the same time.
        # Don't be evil.
        if i%5==0:
            time.sleep(5)
            
    print ("All FilmAffinity thread launched. Waiting for response, it could take a while.")
    
    # Wait for all threads
    i=0
    while i<len(t):
        while t[i].isAlive():
            pass
        i+=1
        
    # Kill ThreadFileAdd.
    queueFA.put('KILL', True)
    
    while not queueFA.empty():
        pass
    
    print ("No FilmAffinity threads alive. Go ahead.")
    
    return oAllData

class ThreadGet(threading.Thread):
    """Threaded Url Grab"""
    
    def __init__(self,urlVotes,webSession,i,queueOut, oAllData):
        threading.Thread.__init__(self)
        self.urlVotes = urlVotes
        self.webSession = webSession
        self.i = i
        self.queueOut = queueOut
        self.oAllData = oAllData
        
    def print_file_add(self,filename, content):
        try:
            fout=open(filename, 'a')
            fout.write(content)
            fout.close
            return 1
        except:
            print("FA Thread critical ERROR: Impossible to open: " + filename)
            return 0
        
        
    def scrapMovie(self, text):
                        
        sOut=""
        
        # text input is HTML code from the votes list. With regular expression we can get the information from all the movies.
        # /!\ If FA web changes you must change this regular expression.
        pattern = re.compile ('Add to lists.*?href="\/en\/(.*?).html">(.*?)<\/a>.*?\((\d*)\).*?<b>(.*?)<\/b>.*?data-user-rating="(\d+)"', re.MULTILINE|re.DOTALL)              
        iterator = pattern.finditer (text)
        
        i=1
        for result in iterator:
            
            # Get the information from the regular expression match.
            title = self.htmlFilter(result.group(2))
            year = result.group(3)
            director = self.htmlFilter(result.group(4))
            vote = result.group(5)
            movieNumber = result.group(1)
            
            # print (title + "    " + year +"    "+vote) # Uncoment to enjoy watching the movies appears (to develop)
            
            self.oAllData.append([title, year, director, vote, movieNumber])
            
            # New movie entry for CSV file.        
            sOut= sOut + title.replace(";", ",") + ";" + year + ";" + director.replace(";",",") + ";" + vote + ";" +  movieNumber +'\n'
            i=i+1
        try:
            recodedsOut=sOut.encode('iso-8859-1', 'replace')
            recodedsOut = recodedsOut.encode('raw_unicode_escape')
            lock=threading.Lock()
            lock.acquire()
            self.queueOut.put(recodedsOut) 
            lock.release()
        except:
            print ("Unexpected error:", sys.exc_info())
            print ("Error queuing: ",recodedsOut)
    
    
    # Important function to escape from HTML special characters (In this case unescape HTML --> regular text).
    def htmlFilter(self, text):
        return saxutils.unescape(text)
    
    # Class main        
    def run(self):
        
        tryNumber=0 
        # Definimos arbitrariamente 5 retries, a mejorar en futuros codigos?
        while tryNumber<=5:
            try:
                webResponse= self.webSession.open(self.urlVotes)
                self.scrapMovie(webResponse.read())
            except:
                # print ("Unexpected error:", sys.exc_info())
                print ("Error getting page: " + str(self.i) + ". Retry: " + str(tryNumber) + " out of 5")
                tryNumber += 1
                continue
            break
        
        if tryNumber>5:
            print ("Max retries:" + str(self.i) + "retry: " + str(tryNumber))

def printFile(filename, content):
    try:
        fout=open(filename, 'w')
        fout.write(content)
        fout.close
        return 1
    except:
        # print("Critical ERROR: Impossible to open: " + filename)
        return 0

class ThreadFileAdd(threading.Thread):
    """Threaded Url Grab"""
    def __init__(self,filename,q):
        threading.Thread.__init__(self)
        self.filename=filename
        self.q=q
        
    def print_file_add(self,filename, content):
        try:
            fout=open(filename, 'a')
            fout.write(content)
            fout.close
            return 1
        except:
            print("FA Thread critical ERROR: Impossible to open: " + filename)
            return 0
        
    def run(self):
        while True:
            self.data=self.q.get(True)
            if self.data=='KILL':
                break                
            self.print_file_add(self.filename, self.data)
            




