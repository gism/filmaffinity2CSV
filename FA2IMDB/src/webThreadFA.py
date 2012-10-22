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

def login():
    
    user, password = getUser()
    
    # Enable cookie support for urllib2
    cookiejar = cookielib.CookieJar()
    webSession = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))

    webSession.open(urlLogin)
        
    dataForm =  {"postback": 1, "rp": "", "user":user, "password":password}
    dataPost = urllib.urlencode(dataForm)

    request = urllib2.Request(urlLogin, dataPost)
    webSession.open(request)  # Our cookiejar automatically receives the cookies
    
    return webSession, cookiejar

def getNumberPagesFA(url, webSession):
    
    webResponse = webSession.open(url)
    
    pattern = re.compile ('Page number <b>1<\/b> of <b>([\d]+)<\/b>[\w\W\s\S]+Number of movies rated: <b>([\d]+)<\/b><\/td><\/tr>')    # Pattern ENGLISH.v1 MUCH BETTER!
    match = pattern.search (webResponse.read())
    
    numPages = match.group(1)
    numVotes = match.group(2)
    
    return numPages, numVotes

def getDataFA(sFilename, oAllData):
    
    global urlVotes    

    webSession, cookiejar = login()
    if len(cookiejar) < 2:
        print ("Login error!: Incorrect FA User or password, please try again.")
        return -1, -1

    # Getting number of pages and movies rated in FA.
    numPages, numVotes = getNumberPagesFA(urlVotes, webSession)
    print ("Looking for {0} movies in {1} pages." .format (numVotes,numPages))
    
    if sFilename != "":
        if not printFile(sFilename, ""):
            print("Critical ERROR! Impossible to open: " + sFilename)
            return -1
    
    t=[]
    i=1
    queueFA=Queue.Queue()
    fileWrite = ThreadFileAdd(sFilename, queueFA)
    if sFilename != "":
        fileWrite.start()
        
    while i<=int(numPages):
    
        print ("Getting page: " + str(i) + " from FA website.")
        urlVotes= urlVotes_prefix + str(i) + urlVotes_sufix + outOrder_title
        
        t.append(ThreadGet(urlVotes, webSession, i, queueFA, oAllData))
        t[i-1].start()
        i+=1
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
        
        # /!\ If FA web changes you must change this regular expression.
        pattern = re.compile ('Add to lists.*href="\/en\/(.*?).html">(.*?)<\/a>.*[\n\r\s]*\((\d*)\)[\n\r\W\w]*?<b>([\w\s\W]*?)<\/b>[\n\r\W\w]*?selected >(\d*)')              
        iterator = pattern.finditer (text)
        
        i=1
        for result in iterator:
            
            title = self.htmlFilter(result.group(2))
            year = result.group(3)
            director = self.htmlFilter(result.group(4))
            vote = result.group(5)
            movieNumber = result.group(1)
            
            self.oAllData.append([title, year, director, vote, movieNumber])
                    
            sOut= sOut + title.replace(";", ",") + ";" + year + ";" + director.replace(";",",") + ";" + vote + ";" +  movieNumber +'\r'
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
            
    def run(self):
        
        tryNumber=0 
        # Definimos arbitrariamente 5 retries, a mejorar en futuros codigos.
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
        
    def htmlFilter(self, text):
        return saxutils.unescape(text)

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
            




