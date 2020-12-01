# filmaffinity2CSV
Backup your filmaffinity votes to local file (CSV)

# How to:
Run main.py using python 3.x (tested on Python 3.8.5)

**Experimental!**
You can backup FA votes to IMDB by:
0 - Set your film affinity user ID and IMDB credentials in config.py
1 - Execute main.py  --> This will create csv file with your FA data
2 - Execute test_vote_imdb.py --> New CSV will be created

Only tested with small movies list. Provably IMDB captcha will be triggered!

# Dependencies:
If error do on windows cmd line: pip install XXXX (ie. pip install bs4)

- http.cookiejar
- re
- threading
- queue
- bs4
- tabulate
- codecs
- warnings
- selenium

Copy chromedriver.exe to you local project folder and solve capchas when required

# Remember:
No argument pass to main. Change config.py with your filmaffinity user id
