# filmaffinity2IMDB
Get filmaffinity voted movies, save them to CSV and post them on IMDB

# How to:
Run main.py using python 2.7 and wait :)

When login to IMDB captcha is required. Open captcha url and type text on python.

# Remember:
You can hardcode your user settings by renaming config.py.example to config.py and updating content.

# About this fork:
This 
https://github.com/txemi/filmaffinity2IMDB
was forked from:
https://github.com/gism/filmaffinity2IMDB
by me with these objectives:
* Reviewing imdb-fa matching code as it was not working sometimes proprely for me.
* Considering evolve this code to get a nice API for getting data from imdb and fa.

I refactorized this code to increase readability and also added a config file not to type password with earch execution.
There is also a selenium version of fa code that I made before knowing about this project and I leave there for reference. I think is better the urllib version unless it would be even better using request python module.
