import logging
import os
import git
import urllib2
import BeautifulSoup
import urimunge
import os.path
import tempfile
import filecmp
import shutil
import subprocess

def uriYieldRpm(uri):
    uri_decomposed = urimunge.setUri(uri)
    pathStack = [uri_decomposed['path']]
    while len(pathStack) > 0:
        uri_decomposed["path"] = pathStack.pop()
        req = urllib2.Request(urimunge.getUri(uri_decomposed))
        page=urllib2.urlopen(req).read()
        soup = BeautifulSoup.BeautifulSoup(page)
        links = soup.findAll("a")
        linkset = set([])
        for link in links:
            linkset.add(link.get("href"))
        for link in linkset:
            link_decomposed = urimunge.setUri(link)
            link_path = link_decomposed.get('path')
            if link_path == None:
                continue
            if len(link_path) < 1:
                continue
            if link_path[0] == '/':
                continue
            if link_path[-1] == '/':
                newpath = "%s%s" % (uri_decomposed["path"],link_path)
                pathStack.append(newpath)
                continue
            link_split = link_path.split('.')
            if link_split[-1] != "rpm":
                continue
            uri_output = dict(uri_decomposed)
            uri_output["path"] = "%s%s" % (uri_decomposed["path"],link_path)
            yield urimunge.getUri(uri_output)


def download_rpm(uri,relpath,log):
    log.info("downloading %s..." % (uri))
    output = False
    tmpfile = tempfile.NamedTemporaryFile()
    uri_ptr = urllib2.urlopen(uri)
    shutil.copyfileobj(uri_ptr, tmpfile)

    if not os.path.exists(relpath):
        output = True

    if output == False:
        if not filecmp.cmp(tmpfile.name, relpath, shallow=False):
            output = True
    if output == True:
        shutil.copyfile(tmpfile.name, relpath)
    return output


class downloader(object):
    def __init__(self,**kwargs):
        self.log = logging.getLogger("downloader")
        self.git_dir = kwargs.get('workingdir', None)
        self.git_origin = kwargs.get('origin', None)
        self.shared_clone = kwargs.get('shared_clone', None)
    def work_dir_setup(self,**kwargs):
        branch = kwargs.get('branch', 'ibs_product_1.0')
        if len(self.shared_clone):
            if not os.path.isdir(self.shared_clone):
                try:
                    self.log.info("cloning from %s..." % (self.git_origin))
                    self.repo = git.Repo.clone_from(self.git_origin, self.shared_clone)
                except git.exc.InvalidGitRepositoryError as E:
                    self.log.warning("failed to clone shared git repo from:%s" % (E.message))

            if not os.path.isdir(self.git_dir):
                self.log.info("creating new workdir %s..." % (self.git_dir))
                if not subprocess.call("git-new-workdir %s %s %s" %
                                       (os.path.abspath(self.shared_clone),
                                        os.path.abspath(self.git_dir),
                                        branch),
                                       shell=True):
                    self.log.warning("failed to load git repo from:%s" % (E.message))

            self.repo = git.Repo(self.git_dir)
        else:
            if not os.path.isdir(self.git_dir):
                try:
                    self.log.info("cloning from %s..." % (self.git_origin))
                    self.repo = git.Repo.clone_from(self.git_origin, self.git_dir )
                except git.exc.InvalidGitRepositoryError as E:
                    self.log.warning("failed to clone git repo from:%s" % (E.message))
            else:
                self.repo = git.Repo(self.git_dir)

        if self.repo.is_dirty():
            self.log.error("Repository is dirty")
            return False

        if len(self.repo.branches) == 0:
            path = "%s/README" % (self.git_dir)
            f = open(path,'w')
            f.write("This master branch has no content.\n\n"
                    "Switch to one of the branches for actual bits.\n\n"
                    "Used to store all successful OBS build artifacts.")
            f.close()
            self.repo.commit()
        self.log.info("checking out branch %s..." % (branch))
        if not branch in self.repo.branches:
            self.repo.git.checkout('master', b=branch)
        else:
            self.repo.git.checkout(branch)

        return True

    def update(self,**kwargs):
        index = self.repo.index
        somethingChanged = False
        uri = kwargs.get('uri', None)
        uri_decomposed = urimunge.setUri(uri)
        for uri_rpm in uriYieldRpm(uri):
            uri_rpm_decomposed = urimunge.setUri(uri_rpm)
            relpath = os.path.relpath(uri_rpm_decomposed["path"],uri_decomposed ["path"])
            newpath = "%s/%s" % (self.git_dir,relpath)
            newfile = False
            if not os.path.exists(newpath):
                newfile = True
                directory = os.path.dirname(newpath)
                if not os.path.isdir(directory):
                    os.makedirs(directory)
            changed = download_rpm(uri_rpm,newpath, self.log)
            if newfile:
                somethingChanged = True
                index.add([relpath])
            if changed:
                self.log.info("uri %s changed" % (uri_rpm))
                somethingChanged = True
            else:
                self.log.debug("uri %s unchanged" % (uri_rpm))
        if somethingChanged:
            index.commit("Updated from OBS repo\n\n%s" % (uri))
        else:
            self.log.info("No changes to the repo")
