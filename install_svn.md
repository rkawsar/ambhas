#Step by step guide to install the library using svn.

# Download svn client #
First you need to have some svn client in order to download using svn. There are various svn available for different platforms.

# Download using svn #
First make a working copy of library in your local repository. The working copy means that you can take content from svn repository, but you can not post to repository. But this is ok, you do not want to upload new files to repository. What? Do you want to upload your new library in the repository, you are welcome, contact us.

```
svn checkout http://ambhas.googlecode.com/svn/trunk/ ambhas
```

# Install #
```
sudo python setup.py install 
```