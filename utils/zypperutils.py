from launch import launch
import logging, os

log = logging.getLogger(__name__)

def addRepo(reponame, url, node):
    if isRepoPresent(reponame, node):
        if getRepoParamValue(reponame, "URI", node) == url:
            log.warn("repo %s with url %s is already present" % (reponame, url))
            zypperRefresh(node)
            return
        else:
            log.warn("repo '%s' is present but with incorrect url, removing the repo" % (reponame))
            removeRepo(reponame, node)
            
    cmd = "ssh %s sudo zypper addrepo %s %s" % (node, url, reponame)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    zypperRefresh(node)

def zypperRefresh(node):
    cmd = "ssh %s sudo zypper --gpg-auto-import-keys --non-interactive refresh" % (node)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)


def isRepoPresent(reponame, node):
    cmd = "ssh %s zypper lr %s" % (node, reponame)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc == 0 and stderr.strip() == "":
        log.info("repo '%s' is present" % (reponame))
        return True
    elif stderr.strip() == "Repository '%s' not found by its alias, number, or URI." % (reponame):
        log.info("repo '%s' is not present" % (reponame))
        return False
    else:
        log.warn("status for repo '%s' could not be validated. Deleting the repo" % (reponame))
        removeRepo(reponame, node)
        return False


def removeRepo(reponame, node):
    cmd = "ssh %s sudo zypper removerepo %s" % (node, reponame)
    log.info("removing the repo '%s'"  % (reponame))
    rc,stdout,stderr = launch(cmd=cmd)
    if rc == 0 and stderr.strip() == "":
        log.info("repo '%s' was removed" % (reponame))
        zypperRefresh(node)
        return True
    else:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    
    
    
def getRepoParamValue(reponame, paramname, node):
    cmd = "ssh %s zypper lr %s" % (node, reponame)
    rc,stdout,stderr = launch(cmd=cmd)
    if stderr.strip() == "Repository '%s' not found by its alias, number, or URI." % (reponame):
        log.info("repo '%s' is not already present"  % (reponame))
        return False
    
    paramdict = {}
    paramlist = stdout.split('\n')
    for i in range (len(paramlist)-2):
        keyvalue = paramlist[i].split(":",1)
        paramdict[keyvalue[0].strip()] = keyvalue[1].strip()
    if paramname not in  paramdict.keys():
        log.warn("parameter name '%s' was not present for repo '%s'" % (paramname, reponame))
        return False
    return paramdict[paramname]


def installPkg(pkgName, node):
    cmd = "ssh %s sudo zypper --non-interactive --no-gpg-checks --quiet install %s"  % (node, pkgName)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)

def installPkgFromRepo(pkgName, node, repo):
    cmd = "ssh %s sudo zypper --non-interactive --no-gpg-checks --quiet install -r %s %s"  % (node, repo, pkgName)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr+stdout)


def removePkg(pkgName, node):
    cmd = "ssh %s sudo zypper --non-interactive --no-gpg-checks --quiet remove %s"  % (node, pkgName)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)


def removePkg_expectNotFound(pkgName, node):
    cmd = "ssh %s sudo zypper --non-interactive --no-gpg-checks --quiet remove %s"  % (node, pkgName)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != (0 or 104):
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)

def removeAllPkgsFromRepo(repoName, node):
    cmd = "ssh %s sudo zypper --non-interactive --no-gpg-checks rm $(ssh %s zypper --disable-system-resolvables \
    -s 0 packages -r %s | tail -n +4 | cut -d'|' -f3 | sort -u)"  % (node, node, repoName)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != (0):
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stdout)
    #log.debug("removed following packages - "+stdout)

def getPkgParamValue(pkgname, paramname, node):
    cmd = "ssh %s zypper info %s" % (node, pkgname)
    rc,stdout,stderr = launch(cmd=cmd)
    if "package '"+pkgname+"' not found." in stdout.strip():
        log.warn("package '%s' is not contained in any repo" % (pkgname))
        raise Exception, "package '%s' is not contained in any repo" % (pkgname)
        
    paramdict = {}
    paramlist = stdout.split('\n')
    for i in range (len(paramlist)-2):
        keyvalue = paramlist[i].split(":",1)
        if len(keyvalue) > 1:
            paramdict[keyvalue[0].strip()] = keyvalue[1].strip()
    if paramname not in  paramdict.keys():
        log.error("parameter name '%s' was not present for repo '%s'" % (paramname, pkgname))
        raise Exception, "parameter name '%s' was not present for repo '%s'" % (paramname, pkgname)
    return paramdict[paramname]
