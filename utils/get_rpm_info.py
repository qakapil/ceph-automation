import urllib
import re

def get_repo_rpms(repo_url):
    text = urllib.urlopen(repo_url).read()
    rpms = re.findall(r'href="(.[^"]*x86_64.rpm).mirrorlist"', text)
