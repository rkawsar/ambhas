# Content #


# Windows #
Currently I am using Python 2.7 and Spyder as IDE. The way to insall them is given here. If you want to use some other version of Python or some other IDE, the procedure should not be much different.

Lets install the Spyder that has Python 2.7. The ways of installation are given at http://code.google.com/p/spyderlib/wiki/Installation. There is one "hard" and one "soft" way. I think it is good to go for soft way. So lets download Python(x,y) from http://code.google.com/p/pythonxy/. You can install it by double clicking and following the procedure. If you face any problem, report there.


Python comes automatically with the Spyder, but for some reason if you want it separately, you can download it from http://www.python.org/download/releases/2.7.3/. Download the version that suits you. I know there are many options and is confusing for a beginner. I think most of the computers are now 64 bit, even if it is not true, you can safely start with it. The version I downloaded is http://www.python.org/ftp/python/2.7.3/python-2.7.3.amd64.msi.


# First Program #
To check if python and Spyder is installed properly, first open the Spyder, and then inside it run the following code.
```
import getpass
username = getpass.getuser()
print("hello to %s! Python in Spyder is working"%username)
```
If you get an error message after running this, please report here.
