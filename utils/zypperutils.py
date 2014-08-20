from launch import launch
import logging, os

log = logging.getLogger(__name__)

def addRepo(reponame, url):
    if isRepoPresent(reponame):
        if getRepoParamValue(reponame, "URI") == url:
            log.warn("repo %s with url %s is already present" % (reponame, url))
            return
        else:
            log.warn("repo '%s' is present but with incorrect url, removing the repo" % (reponame))
            removeRepo(reponame)
            
    cmd = "ssh %s sudo zypper addrepo %s %s" % (os.environ["CLIENTNODE"], url, reponame)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    zypperRefresh()

def zypperRefresh():
    cmd = "ssh %s sudo zypper --gpg-auto-import-keys --non-interactive refresh" % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)


def isRepoPresent(reponame):
    cmd = "ssh %s zypper lr %s" % (os.environ["CLIENTNODE"], reponame)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc == 0 and stderr.strip() == "":
        log.info("repo '%s' is present" % (reponame))
        return True
    elif stderr.strip() == "Repository '%s' not found by its alias, number, or URI." % (reponame):
        log.info("repo '%s' is not present" % (reponame))
        return False
    else:
        log.warn("status for repo '%s' could not be validated. Deleting the repo" % (reponame))
        removeRepo(reponame)
        return False


def removeRepo(reponame):
    cmd = "ssh %s sudo zypper removerepo %s" % (os.environ["CLIENTNODE"], reponame)
    log.info("removing the repo '%s'"  % (reponame))
    rc,stdout,stderr = launch(cmd=cmd)
    if rc == 0 and stderr.strip() == "":
        log.info("repo '%s' was removed" % (reponame))
        return True
    else:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    zypperRefresh()
    
    
    
def getRepoParamValue(reponame, paramname):
    cmd = "ssh %s zypper lr %s" % (os.environ["CLIENTNODE"], reponame)
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


def installPkg(pkgName):
    cmd = "ssh %s sudo zypper --non-interactive --no-gpg-checks --quiet install %s"  % (os.environ["CLIENTNODE"], pkgName)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
def removePkg(pkgName):
    cmd = "ssh %s sudo zypper --non-interactive --no-gpg-checks --quiet remove %s"  % (os.environ["CLIENTNODE"], pkgName)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)


def getPkgParamValue(pkgname, paramname):
    cmd = "ssh %s zypper info %s" % (os.environ["CLIENTNODE"], pkgname)
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
