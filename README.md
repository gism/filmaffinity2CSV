# filmaffinity2CSV
Backup your filmaffinity votes to local file (CSV)

# How to:
Run main.py using python 3.x (tested on Python 3.8.5)

0 - Set your filmaffinity user ID and IMDB credentials in config.py

1 - Execute main.py  --> This will create csv file with your FA data

2 - (Optional) Generate statistical report of FA CSV file: execute generate_stats_report.py 

**Experimental!**
You can back-up FA votes to IMDB by using test_vote_imdb.py

3 - Execute test_vote_imdb.py --> New CSV will be created

Only tested with small movies list. Provably IMDB captcha will be triggered!

# Dependencies:
If error do on Windows cmd line: pip install XXXX (ie. pip install bs4)
- 
- bs4
- tabulate
- selenium

Copy chromedriver.exe to you local project folder and solve captcha when required

# Remember:
No argument pass to main. Change config.py with your filmaffinity user id
