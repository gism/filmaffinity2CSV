#!/usr/bin/python
# -*- coding: latin-1 -*-
import threading
import sys
import re
import Queue

import cookielib, urllib, urllib2
import ast
from difflib import SequenceMatcher as sDiff
import time

# IMDB URL set.
IMDBurlLogin = "https://secure.imdb.com/register-imdb/login#"
IMDBvotedPrefix = "http://www.imdb.com/user/ur5741926/ratings?start="
IMDBvotedSufix = "&view=detail&sort=title:asc&defaults=1&my_ratings=restrict&scb=0.28277816087938845"
IMDBakas = "http://akas.imdb.com/"

# If movie is not found save it anyway.
bSaveNotFound = True

# Put your account information here.
# Or define bAskUser = False if you want to write it each time you run the code.
def getUser():
    
    #bAskUser = False
    bAskUser = True    
        
    if bAskUser:
        sUser = raw_input('Please enter your IMDB USER:')
        sPassword = raw_input('Please enter your IMDB PASSWORD:')
        return sUser, sPassword    
    else:
        return "YourUserHERE" , "YourPasswordHERE"    

def login():
    
    user, password = getUser()
        
    # Enable cookie support for urllib2
    cookiejar = cookielib.CookieJar()
    webSession = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
    
    url = webSession.open(IMDBurlLogin)
    pattern = re.compile ('<input type="hidden" name="([\d\w]+)" value="([\d\w]+)" \/>')
    match = pattern.search (url.read())

    dataForm = {match.group(1):match.group(2), "login":user, "password":password}
    dataPost = urllib.urlencode(dataForm)
    
    request = urllib2.Request("https://secure.imdb.com/register-imdb/login#", dataPost)
    url = webSession.open(request)  # Our cookiejar automatically receives the cookies

    if not 'id' in [cookie.name for cookie in cookiejar]:
        print ("Login error!: Incorrect FA User or password, please try again.")
        return -1, -1
        
    return webSession, cookiejar

def postData(mArrayData, sFilename):
    
    # Web login.
    print("Trying to login at IMDB website and getting credentials:")
    try:   
        webSession, cookiejar = login()
        if (webSession == -1 and cookiejar == -1):
            print ("Impossible to login: Incorrect user/password.")
            return -1
    except:
        print ("Error login at IMDB.")
        print (sys.exc_info())
        return -1
    
    if sFilename != "":    
        if not printFile(sFilename, ""):
            print("Critical ERROR! Impossible to open: " + sFilename)
            return -1
      
    i=0
    postThreads=[]
    queueData=Queue.Queue()
    fileWrite = ThreadFileAdd(sFilename, queueData)
    if sFilename != "":
        fileWrite.start()
    
    while i < len(mArrayData):
        
        postThreads.append(ThreadPostIMDB(webSession, i, queueData, mArrayData))
        postThreads[i].start()
        
        i+=1
        if i%5==0:
            time.sleep(5)
        if i%50==0:
            print (str(i) + "out of: " + str(len(mArrayData)))
           
    print ("All IMDB (Post) thread launched. Waiting for response, it could take a while.")
    
    # Wait for all threads
    i=0
    while i<len(postThreads):
        while postThreads[i].isAlive():
            pass
        i+=1
        
    # Kill ThreadFileAdd.
    queueData.put('KILL', True)
    print ("No IMDB (Post) threads alive. Go ahead.")
    
    return 0

def htmlFilter(text):
    
    # I think this is the whole char table. Bad coding? --> Try to implement it better.
    text = text.replace("&#x09;","")
    text = text.replace("&#x10;","")
    text = text.replace("&#x20;","")
    text = text.replace("&#x21;","!")
    text = text.replace("&#x22;",'"')
    text = text.replace("&#x23;","#")
    text = text.replace("&#x24;","$")
    text = text.replace("&#x25;","%")
    text = text.replace("&#x26;","&")
    text = text.replace("&#x27;","'")
    text = text.replace("&#x28;","(")
    text = text.replace("&#x29;",")")
    text = text.replace("&#x2A;","*")
    text = text.replace("&#x2B;","+")
    text = text.replace("&#x2C;",",")
    text = text.replace("&#x2D;","-")
    text = text.replace("&#x2E;",".")
    text = text.replace("&#x2F;","/")
    text = text.replace("&#x30;","0")
    text = text.replace("&#x31;","1")
    text = text.replace("&#x32;","2")
    text = text.replace("&#x33;","3")
    text = text.replace("&#x34;","4")
    text = text.replace("&#x35;","5")
    text = text.replace("&#x36;","6")
    text = text.replace("&#x37;","7")
    text = text.replace("&#x38;","8")
    text = text.replace("&#x39;","9")
    text = text.replace("&#x3A;",":")
    text = text.replace("&#x3B;",";")
    text = text.replace("&#x3C;","<")
    text = text.replace("&#x3D;","=")
    text = text.replace("&#x3E",">")
    text = text.replace("&#x3F;","?")
    text = text.replace("&#x40;","@")
    text = text.replace("&#x41;","A")
    text = text.replace("&#x42;","B")
    text = text.replace("&#x43;","C")
    text = text.replace("&#x44;","D")
    text = text.replace("&#x45;","E")
    text = text.replace("&#x46;","F")
    text = text.replace("&#x47;","G")
    text = text.replace("&#x48;","H")
    text = text.replace("&#x49;","I")
    text = text.replace("&#x4A;","J")
    text = text.replace("&#x4B;","K")
    text = text.replace("&#x4C;","L")
    text = text.replace("&#x4D;","M")
    text = text.replace("&#x4E;","N")
    text = text.replace("&#x4F;","O")
    text = text.replace("&#x50;","P")
    text = text.replace("&#x51;","Q")
    text = text.replace("&#x52;","R")
    text = text.replace("&#x53;","S")
    text = text.replace("&#x54;","T")
    text = text.replace("&#x55;","U")
    text = text.replace("&#x56;","V")
    text = text.replace("&#x57;","W")
    text = text.replace("&#x58;","X")
    text = text.replace("&#x59;","Y")
    text = text.replace("&#x5A;","Z")
    text = text.replace("&#x5B;","[")
    text = text.replace("&#x5C;","/")
    text = text.replace("&#x5D;","]")
    text = text.replace("&#x5E;","^")
    text = text.replace("&#x5F;","_")
    text = text.replace("&#x60;","`")
    text = text.replace("&#x61;","a")
    text = text.replace("&#x62;","b")
    text = text.replace("&#x63;","c")
    text = text.replace("&#x64;","d")
    text = text.replace("&#x65;","e")
    text = text.replace("&#x66;","f")
    text = text.replace("&#x67;","g")
    text = text.replace("&#x68;","h")
    text = text.replace("&#x69;","i")
    text = text.replace("&#x6A;","j")
    text = text.replace("&#x6B;","k")
    text = text.replace("&#x6C;","l")
    text = text.replace("&#x6D;","m")
    text = text.replace("&#x6E;","n")
    text = text.replace("&#x6F;","o")
    text = text.replace("&#x70;","p")
    text = text.replace("&#x71;","q")
    text = text.replace("&#x72;","r")
    text = text.replace("&#x73;","s")
    text = text.replace("&#x74;","t")
    text = text.replace("&#x75;","u")
    text = text.replace("&#x76;","v")
    text = text.replace("&#x77;","w")
    text = text.replace("&#x78;","x")
    text = text.replace("&#x79;","y")
    text = text.replace("&#x7A;","z")
    text = text.replace("&#x7B;","{")
    text = text.replace("&#x7C;","|")
    text = text.replace("&#x7D;","}")
    text = text.replace("&#x7E;","~")
    text = text.replace("&#x7F;","")
    text = text.replace("&#x80;","€")
    text = text.replace("&#x81;"," ")
    text = text.replace("&#x82;","‚")
    text = text.replace("&#x83;","ƒ")
    text = text.replace("&#x84;","„")
    text = text.replace("&#x85;","…")
    text = text.replace("&#x86;","†")
    text = text.replace("&#x87;","‡")
    text = text.replace("&#x88; ","ˆ")
    text = text.replace("&#x89;","‰")
    text = text.replace("&#x8A;","Š")        
    text = text.replace("&#x8B; ","‹")
    text = text.replace("&#x8C;","Œ")
    text = text.replace("&#x8E;","Ž")
    text = text.replace("&#x91;","‘")
    text = text.replace("&#x92;","’")
    text = text.replace("&#x93;","“")
    text = text.replace("&#x94;","”")
    text = text.replace("&#x95;","•")
    text = text.replace("&#x96;","–")
    text = text.replace("&#x97;","—")
    text = text.replace("&#x98; ","˜")
    text = text.replace("&#x99;","™")
    text = text.replace("&#x9A;","š")
    text = text.replace("&#x9B; ","›")
    text = text.replace("&#x9C;","œ")
    text = text.replace("&#x9E; ","ž")
    text = text.replace("&#xA1;","¡")
    text = text.replace("&#xA2;","¢")
    text = text.replace("&#xA3;","£")
    text = text.replace("&#xA4;","¤")
    text = text.replace("&#xA5;","¥")
    text = text.replace("&#xA6;","¦")
    text = text.replace("&#xA7;","§")
    text = text.replace("&#xA8;","¨")
    text = text.replace("&#xA9;","©")
    text = text.replace("&#xAA;","ª")
    text = text.replace("&#xAB;","«")
    text = text.replace("&#xAC;","¬")
    text = text.replace("&#xAE;","®")
    text = text.replace("&#xAF;","¯")
    text = text.replace("&#xB0;","°")
    text = text.replace("&#xB1;","±")
    text = text.replace("&#xB2;","²")
    text = text.replace("&#xB3;","³")
    text = text.replace("&#xB4;","´")
    text = text.replace("&#xB5;","µ")
    text = text.replace("&#xB6;","¶")
    text = text.replace("&#xB7;","·")
    text = text.replace("&#xB8;","¸")
    text = text.replace("&#xB9;","¹")
    text = text.replace("&#xBA;","º")
    text = text.replace("&#xBB;","»")
    text = text.replace("&#xBC;","¼")
    text = text.replace("&#xBD;","½")
    text = text.replace("&#xBE;","¾")
    text = text.replace("&#xBF;","¿")
    text = text.replace("&#xC0;","À")
    text = text.replace("&#xC1;","Á")
    text = text.replace("&#xC2;","Â")
    text = text.replace("&#xC3;","Ã")
    text = text.replace("&#xC4;","Ä")
    text = text.replace("&#xC5;","Å")
    text = text.replace("&#xC6;","Æ")
    text = text.replace("&#xC7;","Ç")
    text = text.replace("&#xC8;","È")
    text = text.replace("&#xC9;","É")
    text = text.replace("&#xCA;","Ê")
    text = text.replace("&#xCB;","Ë")
    text = text.replace("&#xCC;","Ì")
    text = text.replace("&#xCD;","Í")
    text = text.replace("&#xCE;","Î")
    text = text.replace("&#xCF;","Ï")
    text = text.replace("&#xD0;","Ð")
    text = text.replace("&#xD1;","Ñ")
    text = text.replace("&#xD2;","Ò")
    text = text.replace("&#xD3;","Ó")
    text = text.replace("&#xD4;","Ô")
    text = text.replace("&#xD5;","Õ")
    text = text.replace("&#xD6;","Ö")
    text = text.replace("&#xD7;","×")
    text = text.replace("&#xD8;","Ø")
    text = text.replace("&#xD9;","Ù")
    text = text.replace("&#xDA;","Ú")
    text = text.replace("&#xDB;","Û")
    text = text.replace("&#xDC;","Ü")
    text = text.replace("&#xDD;","Ý")
    text = text.replace("&#xDE;","Þ")
    text = text.replace("&#xDF;","ß")
    text = text.replace("&#xE0;","à")
    text = text.replace("&#xE1;","á")
    text = text.replace("&#xE2;","â")
    text = text.replace("&#xE3;","ã")
    text = text.replace("&#xE4;","ä")
    text = text.replace("&#xE5;","å")
    text = text.replace("&#xE6;","æ")
    text = text.replace("&#xE7;","ç")
    text = text.replace("&#xE8;","è")
    text = text.replace("&#xE9;","é")
    text = text.replace("&#xEA;","ê")
    text = text.replace("&#xEB;","ë")
    text = text.replace("&#xEC;","ì")
    text = text.replace("&#xED;","í")
    text = text.replace("&#xEE;","î")
    text = text.replace("&#xEF;","ï")
    text = text.replace("&#xF0;","ð")
    text = text.replace("&#xF1;","ñ")
    text = text.replace("&#xF2;","ò")
    text = text.replace("&#xF3;","ó")
    text = text.replace("&#xF4;","ô")
    text = text.replace("&#xF5;","õ")
    text = text.replace("&#xF6;","ö")
    text = text.replace("&#xF7;","÷")
    text = text.replace("&#xF8;","ø")
    text = text.replace("&#xF9;","ù")
    text = text.replace("&#xFA;","ú")
    text = text.replace("&#xFB;","û")
    text = text.replace("&#xFC;","ü")
    text = text.replace("&#xFD;","ý")
    text = text.replace("&#xFE;","þ")
    text = text.replace("&#xFF;","ÿ")
    
    # Data lost (Code in UTF-8):
    text = text.replace("&#x8D;","#")
    text = text.replace("&#x8F;","#")
    text = text.replace("&#x90;","#")
    text = text.replace("&#x9D;","#")
    text = text.replace("&#xA0;","#")
    text = text.replace("&#xAD;","#")
                 
    return text

# IMDB suggestion when writing the tittle.
def cleanTitle(sTitle):
    lEnd = sTitle.find("(",1)
    if lEnd==-1:
        return sTitle
    else:
        return sTitle[0:lEnd]

def checkTitle(htmlCode, title, year):
    print("FIRE!")
    start = htmlCode.find("(")
    htmlCode= htmlCode[start+1:-1]

    try:    
        htmlCode = ast.literal_eval(htmlCode)    
    except:
        print ("EVAL Error: ", htmlCode)
        return 0, "tt0000000", "Unknow Title", "0000"
    
    # "d" list contain an dictionary with all suggestion. Nice! this is what we want!
    for a in htmlCode["d"]:
        print (a["id"], a["l"], a["y"])
        if ("y" in a):
            ratio = sDiff(None, title, a["l"]).ratio()
            if (a["y"] == int(year) and ratio > 0.8):
                print ("Found: ", a["id"], a["l"], a["y"]) 
                return 1, a["id"], a["l"], a["y"]
            return 0, "tt0000000", "Unknow Title", "0000"    
    
def getSuggestionCode(urlOpener, cookiejar, movieTittle, movieYear):
    
    NewCookie = cookielib.CookieJar()
    URLchannel = urllib2.build_opener(urllib2.HTTPCookieProcessor(NewCookie))
    
    URLchannel.open(IMDBakas)

    sTitle = cleanTitle(movieTittle)
    
    sSearchString = sTitle + " " + movieYear
    sSearchString =str(sSearchString)
    sSearchString = sSearchString.replace(" ", "_")
    sSearchString = sSearchString.replace(",","")
    sSearchString = sSearchString.replace(".","")
    
    bFound = 0
    j=0
    while j <2 and not bFound:
        i=1
        
        while i<len(sSearchString) and not bFound:
            urlAdr = "http://sg.media-imdb.com/suggests/" + sSearchString[0:1] + "/" + sSearchString[0:i] + ".json"
            try:
                sURLcode = URLchannel.open(urlAdr)
                bFound, foundCode, foundTitle, foundYear = checkTitle(sURLcode.read(), sTitle, movieYear)
            except:
                foundCode ="tt0000000"
                foundTitle = "Movie not found."
                foundYear = "0000"
                print ("No response from URL: ", urlAdr)
            i+=1
        j+=1
    print (foundCode, foundTitle, foundYear)
    return foundCode, foundTitle, foundYear

# Class to GET data from IMDB
class ThreadGetIMDB(threading.Thread):
    """Threaded Url Grab"""
    def __init__(self, urlvotes, s, i, q, oAllData):
        threading.Thread.__init__(self)
        self.urlvotes=urlvotes
        self.s=s
        self.i=i
        self.q = q
        self.oAllData = oAllData
        
    def print_file_add(self,filename, content):
        fout=open(filename, 'a')
        fout.write(content)
        fout.close
        
    def filtro(self,text):
        
        sOut=""
        pattern = re.compile ('<div class="number">(\d+).<\/div>[\w\W\s\S]*?<div class="clear">&nbsp;<\/div>[\n\r]*<\/div>')    # Find all elements
        iterator = pattern.finditer (text)
                
        for element in iterator:
            patternCommon = re.compile('\/tt(\d*)\/"\s*>(.*?)<\/a>\s+<span class="year_type">\((\d*).*?\)<\/span><\/b>[\w\W\s\S]*?<span class="value">(\d+)<\/span><span class="grey">')
            patternDir = re.compile('<div class="secondary">Director: <a href="\/name\/nm\d+\/">(.*?)<\/a><\/div>')
            match = patternCommon.search (element.group(0))
            
            print ("Element: " + element.group(1) + " read." )                     
            title =  htmlFilter(match.group(2))
            year = match.group(3)
            vote = match.group(4)
            movieCode = "tt" + str(match.group(1))
                        
            match = patternDir.search (element.group(0))
                        
            try:
                directors = re.split('<\/a>, <a href="\/name/nm\d+\/">', match.group(1))
                director = ""
                for nameDir in directors:
                    director = director + ", " + htmlFilter(nameDir)
                director = director[2:]
            except:
                director = "N/A"
            sOut= sOut + title.replace(";", ",") + ";" + year + ";" + director.replace(";",",") + ";" + vote + ";" + movieCode + '\r'
        try:
            recodedsOut=sOut.encode('iso-8859-1')
            lock=threading.Lock()
            lock.acquire()
            self.q.put(recodedsOut)
            lock.release()
        except:
            print ("Unexpected error:", sys.exc_info())
            print ("Error queuing: ",recodedsOut)
                    
    def run(self):
        trynumber=1 
        # Definimos arbitrariamente 5 retries, a mejorar en futuros codigos.
        while trynumber<=5:
            try:
                r= self.s.open(self.urlvotes)
            except:
                print ("error geting " + str(self.i) + " page information.")
            try:
                self.filtro(r.read())
            except:
                print ("Unexpected error:", sys.exc_info())
                print (self.urlvotes)
                print ("error en la pagina:" + str(self.i) + "retry" + str(trynumber))
                trynumber+=1
                continue
            break
        if trynumber>5:
            print ("Max retries:" + str(self.i) + "retry: " + str(trynumber))
        
def getData(oAllData, sFileName):
    
    webSession, cookiejar = login()
    
    urlAdr = IMDBvotedPrefix + str(1) + IMDBvotedSufix
    url = webSession.open(urlAdr)
    
    if sFileName != "":
        if not printFile(sFileName, ""):
            print("Critical ERROR! Impossible to open: " + sFileName)
            return -1
    
    pattern = re.compile ('Page 1 of (\d)+')    # Get number of pages
    match = pattern.search (url.read())
    numPages = match.group(1)
    
    t=[]
    i=1
    qIMDB=Queue.Queue()
    fileWrite=ThreadFileAdd(sFileName, qIMDB)
    if sFileName != "":
        fileWrite.start()
    while i <= int(numPages):
        print ("Getting page: {0} out of {1} from IMDB website." .format(i, numPages))
        imdb_page = 1 + (i - 1) * 100
        urlvotes= IMDBvotedPrefix + str(imdb_page) + IMDBvotedSufix
        t.append(ThreadGetIMDB(urlvotes, webSession, i, qIMDB, oAllData))
        t[i-1].start()
        i+=1
        if i%50==0:
            time.sleep(5)
    print ("All IMDB thread launched. Waiting for response, it could take a while.")

    # Wait for all threads
    i=0
    while i<len(t):
        while t[i].isAlive():
            pass
        i+=1
        
    # Kill ThreadFileAdd.
    qIMDB.put('KILL', True)
    print ("No IMDB threads alive. Go ahead.")
    
    return 0

def getMovieCode(urlOpener, mTitle, mYear):
    
    findList = []
    
    sUrlAdd = urllib.urlencode({'q': mTitle, 's': 'all'})    
    urlAdr = IMDBakas + "find?" + sUrlAdd
    
    try:
        url = urlOpener.open(urlAdr)
    except:
        return "ee0000000", "Connection error", 0
        
    urlAdrRed = url.geturl()
    if urlAdrRed.find("/title/tt") != -1:
        
        mCode = urlAdrRed[urlAdrRed.find("/title/tt") + len("/title/tt") -2:urlAdrRed.find("/title/tt") + len("/title/tt") + 7]
        pattern = re.compile ('itemprop="name">([\W\w]*?)<span class="nobr">[\n\w\W]*?\((<a href="\/year\/\d+\/">)?(\d+)(<\/a>)?\)<\/span>')
        match = pattern.search (url.read())
        try:
            movieTitle = match.group(1)
            movieTitle = movieTitle.replace("\n", "")
            movieTitle = htmlFilter(movieTitle)
        except:
            movieTitle = "Not Found"
        try:
            movieYear = match.group(2)
            movieYear = movieYear.replace("\n","")
        except:
            movieYear = "0"
            
        return mCode, movieTitle, movieYear
            
    else:
        pattern = re.compile ('link=\/title\/tt(\d+)\/' + "'" + ';">([\w\W]+?)<\/a>\s\((\d+)[\w\W]*?\)([\w\W]+?)<\/td>')
        iterator = pattern.finditer (url.read())
    
        for result in iterator:
            
            movieCode = "tt" + str(result.group(1))
            movieYear = result.group(3)
            
            movieTitle = result.group(2)
            movieTitle = htmlFilter(movieTitle)
            badCapture = movieTitle.find(';">')
            while badCapture != -1:
                # While used to fix problems with results with images (Remember KISS).
                movieTitle = movieTitle[badCapture+3:]
                badCapture = movieTitle.find(';">')
            
            titleRatio = sDiff(None, mTitle, movieTitle).ratio()
            
            findList.append({'code': movieCode, 'title' : movieTitle, 'year' : movieYear, 'ratio' : titleRatio})
            
            # Find AKAS tittles.
            pattern = re.compile ('aka "([\w\W]+?)"')
            akasIterator = pattern.finditer (result.group(4))
            
            for akaResult in akasIterator:
                akaTitle = akaResult.group(1)
                akaTitle = htmlFilter(akaTitle)
                titleRatio = sDiff(None, mTitle, akaTitle).ratio()
                findList.append({'code': movieCode, 'title' : akaTitle, 'year' : movieYear, 'ratio' : titleRatio})
        
        bestResult = {'code': 'nm0000000', 'title' : 'No match', 'year' : '0', 'ratio' : 0}
        
        
        for movie in findList:
            if abs(int(movie['year']) - int(mYear)) <= 1:
                if bestResult['ratio'] < movie['ratio']:
                    bestResult['code'] = movie['code']
                    bestResult['title'] = movie['title']
                    bestResult['year'] = movie['year']
                    bestResult['ratio'] = movie['ratio']
            
        if     bestResult['ratio']> 0.5:
            return     bestResult['code'], bestResult['title'], bestResult['year']
        else:
            return "bm0000000", "Bad matches", 0

def voteMovie(webSession, mCode, mVote):
        
    urlAdr = IMDBakas + "title/" + mCode + "/"
    urlCode = webSession.open(urlAdr)
    
    pattern = re.compile ('\/vote\?v='+ str(mVote) +';k=([\w\d_-]+)" title="Click to rate:')
    
    content = urlCode.read()
    iterator = pattern.finditer(content)
        
    i=0
    for element in iterator:
        voteHash = element.group(1)
        i=i+1  
    
    urlAdr = IMDBakas + "title/" + mCode + "/vote?v=" + str(mVote) + ";k=" + voteHash
    
    try:    
        webSession.open(urlAdr)
        return 1
    except:
        return -1
  
# Class to put data to IMDB
class ThreadPostIMDB(threading.Thread):
    """Threaded Url Grab"""
    def __init__(self, webSession, i, postQueue, mArrayData):
        threading.Thread.__init__(self)
        self.webSession = webSession
        self.i = i
        self.postQueue = postQueue
        self.mArrayData = mArrayData
                     
    def run(self):
        
        maxRetries = 2
                
        mTitle = self.mArrayData[self.i][0]
        mYear = self.mArrayData[self.i][1]
        mVote = self.mArrayData[self.i][3]
        
        mTitle = cleanTitle(mTitle)
        # Definimos arbitrariamente 3 retries, a mejorar en futuros codigos.
        retryNumber=0 
        while retryNumber < maxRetries:
            try:
                mCode, mTitle, mYear= getMovieCode(self.webSession, mTitle, mYear)
                break
            except:
                print ("Impossible to get movie code: [{0}]: {1} ({2})." .format (self.i, mTitle, mYear))
                retryNumber += 1
                continue
                        
        if retryNumber >= maxRetries:
            print  ("Max retries getting the movie code: [{0}]: {1} ({2})." .format (self.i, mTitle, mYear))
            retryNumber += 1
            # return -1
        
        retryNumber=0 
        while retryNumber < maxRetries:
            try:
                if (voteMovie(self.webSession, mCode, mVote)):
                    break
                else:
                    retryNumber += 1
            except:
                print ("Impossible to post movie vote : [{0}]: {1} ({2})." .format (self.i, mTitle, mYear))
                retryNumber += 1
                continue
            
        if retryNumber >= maxRetries:
            print  ("Max retries posting the movie vote: [{0}]: {1} ({2})." .format (self.i, mTitle, mYear))
            # return -1
        
        # print(self.mArrayData[self.i][0], mTitle, mYear, mCode)
        
        self.mArrayData[self.i].append(mTitle)
        self.mArrayData[self.i].append(mYear)
        self.mArrayData[self.i].append(mCode)
        
        sLine =""
        for entry in self.mArrayData[self.i]:
            sLine = sLine + str(entry) + ";"
        sLine= sLine[0:-1] + "\r"
        self.postQueue.put(sLine)    

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
    def __init__(self, sFilename, queueData):
        threading.Thread.__init__(self)
        self.sFilename=sFilename
        self.queueData=queueData
        
    def fileAddEntry(self, sFilename, content):
        try:
            fout=open(sFilename, 'a')
            fout.write(content)
            fout.close
            return 1
        except:
            print("FA Thread critical ERROR: Impossible to open: " + sFilename)
            return 0
        
    def run(self):
        while True:
            dataEntry = self.queueData.get(True)
            if dataEntry=='KILL':
                break                
            self.fileAddEntry(self.sFilename, dataEntry)