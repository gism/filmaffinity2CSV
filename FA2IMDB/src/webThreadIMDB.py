#!/usr/bin/python
# -*- coding: utf-8 -*-
import threading
import sys
import re
import Queue

import cookielib, urllib, urllib2
import ast
from difflib import SequenceMatcher as sDiff
import time

from xml.dom import minidom

# IMDB URL set.
IMDBurlLogin = "https://secure.imdb.com/register-imdb/login#"
IMDBvotedPrefix = "http://www.imdb.com/user/ur5741926/ratings?start="
IMDBvotedSufix = "&view=detail&sort=title:asc&defaults=1&my_ratings=restrict&scb=0.28277816087938845"
IMDBakas = "http://akas.imdb.com/"
IMDBbyTitleAPI = "http://www.imdb.com/xml/find?xml=1&nr=1&tt=on&"

# If movie is not found save it anyway.
bSaveNotFound = True

# Put your account information here and bAskUser = true.
# Or define bAskUser = False if you want to write it each time you run the code.
def getUser():
    
    #bAskUser = False
    bAskUser = True    
        
    if bAskUser:
        sUser = raw_input('Please enter your IMDB USER:')
        sPassword = raw_input('Please enter your IMDB PASSWORD:')
        return sUser, sPassword    
    else:
        
        return "YourUserHere" , "YourPasswordHere"    

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
        print ("Login error!: Incorrect IMDB User or password, please try again.")
        return -1, -1
        
    return webSession, cookiejar

def postData(mArrayData, sFilename):
    
    # Web login.
    print("Trying to login at IMDB website and getting credentials:")
    try:   
        webSession, cookiejar = login()
        if (webSession == -1 and cookiejar == -1):
            print ("Impossible to login: Incorrect user/password.")
            return
    except:
        print ("Error login at IMDB.")
        print (sys.exc_info())
        return -1
    print("Login: correct.")
    print("")
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
            
    # print mArrayData
    while i < len(mArrayData):
        
        
        postThreads.append(ThreadPostIMDB(webSession, i, queueData, mArrayData))
        postThreads[i].start()
        
        i+=1
        if i%5==0:
            time.sleep(5)
        if i%50==0:
            print (str(i) + " out of: " + str(len(mArrayData)))
           
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
    text = text.replace("&#x80;","?")
    text = text.replace("&#x81;"," ")
    text = text.replace("&#x82;","?")
    text = text.replace("&#x83;","?")
    text = text.replace("&#x84;","?")
    text = text.replace("&#x85;","?")
    text = text.replace("&#x86;","?")
    text = text.replace("&#x87;","?")
    text = text.replace("&#x88;?","?")
    text = text.replace("&#x89;","?")
    text = text.replace("&#x8A;","?")        
    text = text.replace("&#x8B;?","?")
    text = text.replace("&#x8C;","?")
    text = text.replace("&#x8E;","?")
    text = text.replace("&#x91;","?")
    text = text.replace("&#x92;","?")
    text = text.replace("&#x93;","?")
    text = text.replace("&#x94;","?")
    text = text.replace("&#x95;","?")
    text = text.replace("&#x96;","?")
    text = text.replace("&#x97;","?")
    text = text.replace("&#x98;?","?")
    text = text.replace("&#x99;","?")
    text = text.replace("&#x9A;","?")
    text = text.replace("&#x9B;?","?")
    text = text.replace("&#x9C;","?")
    text = text.replace("&#x9E;?","?")
    text = text.replace("&#xA1;","?")
    text = text.replace("&#xA2;","?")
    text = text.replace("&#xA3;","?")
    text = text.replace("&#xA4;","?")
    text = text.replace("&#xA5;","?")
    text = text.replace("&#xA6;","?")
    text = text.replace("&#xA7;","?")
    text = text.replace("&#xA8;","?")
    text = text.replace("&#xA9;","?")
    text = text.replace("&#xAA;","?")
    text = text.replace("&#xAB;","?")
    text = text.replace("&#xAC;","?")
    text = text.replace("&#xAE;","?")
    text = text.replace("&#xAF;","?")
    text = text.replace("&#xB0;","?")
    text = text.replace("&#xB1;","?")
    text = text.replace("&#xB2;","?")
    text = text.replace("&#xB3;","?")
    text = text.replace("&#xB4;","?")
    text = text.replace("&#xB5;","?")
    text = text.replace("&#xB6;","?")
    text = text.replace("&#xB7;","?")
    text = text.replace("&#xB8;","?")
    text = text.replace("&#xB9;","?")
    text = text.replace("&#xBA;","?")
    text = text.replace("&#xBB;","?")
    text = text.replace("&#xBC;","?")
    text = text.replace("&#xBD;","?")
    text = text.replace("&#xBE;","?")
    text = text.replace("&#xBF;","?")
    text = text.replace("&#xC0;","?")
    text = text.replace("&#xC1;","?")
    text = text.replace("&#xC2;","?")
    text = text.replace("&#xC3;","?")
    text = text.replace("&#xC4;","?")
    text = text.replace("&#xC5;","?")
    text = text.replace("&#xC6;","?")
    text = text.replace("&#xC7;","?")
    text = text.replace("&#xC8;","?")
    text = text.replace("&#xC9;","?")
    text = text.replace("&#xCA;","?")
    text = text.replace("&#xCB;","?")
    text = text.replace("&#xCC;","?")
    text = text.replace("&#xCD;","?")
    text = text.replace("&#xCE;","?")
    text = text.replace("&#xCF;","?")
    text = text.replace("&#xD0;","?")
    text = text.replace("&#xD1;","?")
    text = text.replace("&#xD2;","?")
    text = text.replace("&#xD3;","?")
    text = text.replace("&#xD4;","?")
    text = text.replace("&#xD5;","?")
    text = text.replace("&#xD6;","?")
    text = text.replace("&#xD7;","?")
    text = text.replace("&#xD8;","?")
    text = text.replace("&#xD9;","?")
    text = text.replace("&#xDA;","?")
    text = text.replace("&#xDB;","?")
    text = text.replace("&#xDC;","?")
    text = text.replace("&#xDD;","?")
    text = text.replace("&#xDE;","?")
    text = text.replace("&#xDF;","?")
    text = text.replace("&#xE0;","?")
    text = text.replace("&#xE1;","?")
    text = text.replace("&#xE2;","?")
    text = text.replace("&#xE3;","?")
    text = text.replace("&#xE4;","?")
    text = text.replace("&#xE5;","?")
    text = text.replace("&#xE6;","?")
    text = text.replace("&#xE7;","?")
    text = text.replace("&#xE8;","?")
    text = text.replace("&#xE9;","?")
    text = text.replace("&#xEA;","?")
    text = text.replace("&#xEB;","?")
    text = text.replace("&#xEC;","?")
    text = text.replace("&#xED;","?")
    text = text.replace("&#xEE;","?")
    text = text.replace("&#xEF;","?")
    text = text.replace("&#xF0;","?")
    text = text.replace("&#xF1;","?")
    text = text.replace("&#xF2;","?")
    text = text.replace("&#xF3;","?")
    text = text.replace("&#xF4;","?")
    text = text.replace("&#xF5;","?")
    text = text.replace("&#xF6;","?")
    text = text.replace("&#xF7;","?")
    text = text.replace("&#xF8;","?")
    text = text.replace("&#xF9;","?")
    text = text.replace("&#xFA;","?")
    text = text.replace("&#xFB;","?")
    text = text.replace("&#xFC;","?")
    text = text.replace("&#xFD;","?")
    text = text.replace("&#xFE;","?")
    text = text.replace("&#xFF;","?")
    
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


from bs4 import BeautifulSoup

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
        sOut.encode('utf-8')
        pattern = re.compile ('<div class="number">(\d+).<\/div>[\w\W\s\S]*?<div class="clear">&nbsp;<\/div>[\n\r]*<\/div>')    # Find all elements
        iterator = pattern.finditer (text)
                
        for element in iterator:
            patternCommon = re.compile('\/tt(\d*)\/"\s*>(.*?)<\/a>\s+<span class="year_type">\((\d*).*?\)<\/span><\/b>[\w\W\s\S]*?<span class="value">(\d+)<\/span><span class="grey">')
            patternDir = re.compile('<div class="secondary">Director: <a href="\/name\/nm\d+\/">(.*?)<\/a><\/div>')
            match = patternCommon.search (element.group(0))
            
            print ("Element: " + element.group(1) + " read." )                     
            title = match.group(2)  #htmlFilter(match.group(2))
            year = match.group(3)
            vote = match.group(4)
            movieCode = "tt" + str(match.group(1))
                        
            match = patternDir.search (element.group(0))
                        
            try:
                directors = re.split('<\/a>, <a href="\/name/nm\d+\/">', match.group(1))
                director = ""
                for nameDir in directors:
                    director = director + ", " + nameDir #htmlFilter(nameDir)
                director = director[2:]
            except:
                director = "N/A"
            sOut= sOut + title.replace(";", ",") + ";" + year + ";" + director.replace(";",",") + ";" + vote + ";" + movieCode + '\n'
        try:
            soup = BeautifulSoup(sOut.decode('utf-8'))
            recodedsOut = unicode(soup)
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
    
    # Check output file
    if sFileName != "":
        if not printFile(sFileName, ""):
            print("Critical ERROR! Impossible to open: " + sFileName)
            return -1
    
    pattern = re.compile ('Page 1 of (\d+)')    # Get number of pages
    match = pattern.search (url.read())
    numPages = match.group(1)
        
    t=[]
    i=1
    qIMDB = Queue.Queue()
    fileWrite = ThreadFileAdd(sFileName, qIMDB)
    if sFileName != "":
        fileWrite.start()
        
    while i <= 2: #int(numPages):
        print ("Getting page: {0} out of {1} from IMDB website." .format(i, numPages))
        imdb_page = 1 + (i - 1) * 100
        urlvotes= IMDBvotedPrefix + str(imdb_page) + IMDBvotedSufix
        t.append(ThreadGetIMDB(urlvotes, webSession, i, qIMDB, oAllData))
        t[i-1].start()
        i+=1
        if i%10==0:
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
        return "ce0000000", "Connection error", 0
        
    urlAdrRed = url.geturl()
    urlHTML = url.read()
        
    if urlAdrRed.find("/title/tt") != -1:
        
        mCode = urlAdrRed[urlAdrRed.find("/title/tt") + len("/title/tt") -2:urlAdrRed.find("/title/tt") + len("/title/tt") + 7]
        pattern = re.compile ('itemprop="name">([\W\w]*?)<span class="nobr">[\n\w\W]*?\((<a href="\/year\/\d+\/">)?(\d+)(<\/a>)?\)<\/span>')
        
        match = pattern.search (urlHTML)
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
        
        pattern = re.compile ('"result_text"> <a href="\/title\/(tt\d+).*?>(.+?)<\/a>.*?\((\d+)\)', re.MULTILINE|re.DOTALL)
        iterator = pattern.finditer (urlHTML)
        
        for result in iterator:
               
            movieCode = str(result.group(1))
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
        pattern = re.compile ('"result_text"> <a href="\/title\/(tt\d+).*?\((\d+)\).*?aka.*?"(.*?)"', re.MULTILINE|re.DOTALL)
        akasIterator = pattern.finditer (urlHTML)
            
        for akaResult in akasIterator:
                akaTitle = akaResult.group(3)
                akaTitle = htmlFilter(akaTitle)
                
                akaYear = akaResult.group(2)
                akaMovieCode = akaResult.group(1)
                
                titleRatio = sDiff(None, mTitle, akaTitle).ratio()
                findList.append({'code': akaMovieCode, 'title' : akaTitle, 'year' : akaYear, 'ratio' : titleRatio})
                
        # Get the best match
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

def getMovieCodeByAPI(urlOpener, mTitle, mYear):
    
    findList = []
    
    sUrlAdd = urllib.urlencode({'q': mTitle})    
    urlAdr = IMDBbyTitleAPI + sUrlAdd
    try:
        url = urlOpener.open(urlAdr)
    except:
        print("UrlOpener error: Unable to open: " + urlAdr)
        return "ce0000000", "Connection error", 0
    
    IMDBfoundAPI = minidom.parseString(url.read()) 
    movies = IMDBfoundAPI.getElementsByTagName("ImdbEntity")
    
    
    for movie in movies:
        description = movie.getElementsByTagName("Description")
        for a in description:
            if (a.childNodes[0].nodeValue[:4]).isnumeric:
                # Some times isnumeric is not working ¿unicode type problem?
                sYear = a.childNodes[0].nodeValue[:4]
                sYear =filter(type(sYear).isdigit, sYear)
                sYear = "0" + sYear
                year = int(sYear)
        
        movieFoundTitle = movie.childNodes[0].nodeValue
        movieFoundYear = year
        movieFoundCode = movie.getAttribute("id")
        
        titleRatio = sDiff(None, mTitle, movieFoundTitle).ratio()
        
        # print("API: " + str(movieFoundTitle) + " | " + str(movieFoundYear) + " | " + str(movieFoundCode) + " | Ratio: " + str(titleRatio))
        findList.append({'code': movieFoundCode, 'title' : movieFoundTitle, 'year' : movieFoundYear, 'ratio' : titleRatio})
        
                   
    # Get the best match
    bestResult = {'code': 'nm0000000', 'title' : 'No match', 'year' : '0', 'ratio' : 0}       
    for movie in findList:
        if abs(int(movie['year']) - int(mYear)) <= 1:
            if bestResult['ratio'] < movie['ratio']:
                bestResult['code'] = movie['code']
                bestResult['title'] = movie['title']
                bestResult['year'] = movie['year']
                bestResult['ratio'] = movie['ratio']
            
    if bestResult['ratio']> 0.5:
        return bestResult['code'], bestResult['title'], bestResult['year']
    
    else:
        # This is a very optimistic way of think, but for my movie list it works nice.
        if str(findList[0]['year']) == mYear:
            optimistic_code = findList[0]['code']
            optimistic_title = findList[0]['title']
            optimistic_year = findList[0]['year']
            return optimistic_code, optimistic_title, optimistic_year
        else:
            # No result.
            return None, None, None

def voteMovie(webSession, mCode, mVote):
        
    urlAdr = IMDBakas + "title/" + mCode + "/"
    urlCode = webSession.open(urlAdr)
    content = urlCode.read()
    
    pattern = re.compile (mCode + '\/vote\?v='+ str(mVote) +';k=(.*?)" title="Click to rate:')  
    iterator = pattern.finditer(content)
        
    i=0
    for element in iterator:
        voteHash = element.group(1)
        i=i+1
    
    urlAdr = IMDBakas + "title/" + mCode + "/vote?v=" + str(mVote) + ";k=" + voteHash
    
    try:    
        urlCode = webSession.open(urlAdr)
        
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
        
        # Definimos arbitrariamente 3 retries, a mejorar en futuros codigos.
        maxRetries = 2
        
        # Check if the CSV row has all the fields, just to avoid ugly errors
        if len(self.mArrayData[self.i]) < 4:
            print("Error on CVS file: Missing field")
            return            
        
        mTitle = self.mArrayData[self.i][0]
        mYear = self.mArrayData[self.i][1]
        mVote = self.mArrayData[self.i][3]
        
        mTitle = cleanTitle(mTitle)
        
        # print ("<IMDB> Movie to vote: " + "[id: " + str(self.i) + "] " + mTitle + " | " + mYear + " | " + mVote)
        
        retryNumber=0 
        while retryNumber < maxRetries:
            try:
                mCodeFound, mTitleFound, mYearFound= getMovieCodeByAPI(self.webSession, mTitle, mYear)
                
                # Many times IMDB API does not find the result: This is my custom function
                if not mCodeFound:
                    # print("<IMDB> API failed: lets try custom function." + "[id: " + str(self.i) + "] ")
                    mCodeFound, mTitleFound, mYearFound= getMovieCode(self.webSession, mTitle, mYear)
                break
            except:
                print ("Impossible to get movie code [id: {0}]: {1} ({2})." .format (self.i, mTitle, mYear))
                retryNumber += 1
                continue
                        
        if retryNumber >= maxRetries:
            print  ("Max retries getting the movie code [id: {0}]: {1} ({2})." .format (self.i, mTitle, mYear))
            retryNumber += 1
            # return -1
        
        retryNumber=0 
        while retryNumber < maxRetries:
            try:
                if (voteMovie(self.webSession, mCodeFound, mVote)):
                    break
                else:
                    retryNumber += 1
            except:
                print ("Impossible to post movie vote [id: {0}]: {1} ({2})." .format (self.i, mTitle, mYear))
                retryNumber += 1
                continue
            
        if retryNumber >= maxRetries:
            print  ("Max retries posting the movie vote [id: {0}]: {1} ({2})." .format (self.i, mTitle, mYear))
            # return -1
        
        # print(self.mArrayData[self.i][0], mTitle, mYear, mCode)
              
        self.mArrayData[self.i].append(mTitleFound)
        self.mArrayData[self.i].append(mYearFound)
        self.mArrayData[self.i].append(mCodeFound)
        
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
            
def test():
    print ("This is just a test")
    cookiejar = cookielib.CookieJar()
    webSes = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
    
    mTitle = "A Clockwork Orange"
    mYear = "1971"
    
    mCodeFound, mTitleFound, mYearFound= getMovieCodeByAPI(webSes, mTitle, mYear)
    print("RESULT: " + str(mCodeFound) + " | " + str(mTitleFound) + " | " + str(mYearFound))     
    #mCodeFound, mTitleFound, mYearFound= getMovieCode(webSes, mTitle, mYear)
    
# test()
    