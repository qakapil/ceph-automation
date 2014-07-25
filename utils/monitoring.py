from launch import launch
import logging
import ConfigParser
import cephdeploy
import re

log = logging.getLogger(__name__)



def getCephHealth():
    cmd = 'ceph health'
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    log.info('Ceph health is - '+stdout)
    return stdout

def getFSID():
    cmd = 'ceph-conf --lookup fsid'
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    fsid = stdout.strip()
    log.info('ceph fsid is - '+fsid)
    return fsid




def getCephStatus():
    cmd = 'ceph --status'
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    log.info('ceph status is - '+stdout)
    return stdout.strip()


    
def getExpectedVersion(url):
    url = url+'src'
    cmd = 'wget -q -O- %s | grep ceph-0 | sed -e "s|.*ceph-\\(.*\\).src.rpm.*|\\1|"' % (url)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    ceph_version = stdout.strip()
    log.info('Ceph expected version is - '+ceph_version)
    return ceph_version


def getActuaVersion():
    cmd = 'ceph --version'
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    ceph_version = stdout.strip()
    matchObj = re.match( r'ceph version (.*) .*', ceph_version, re.M|re.I)
    ceph_version = matchObj.group(1)
    log.info('Ceph actual version is - '+ceph_version)
    return ceph_version

def printRPMVersions(url):
    ceph_ver = getExpectedVersion(url)
    log.info("The rpm version of ceph is "+ ceph_ver)
    print ("The rpm version of ceph is "+ ceph_ver)
    
    cephdeploy_ver = cephdeploy.getExpectedVersion(url)
    log.info("The rpm version of ceph is "+ cephdeploy_ver)
    print ("The rpm version of ceph is ' "+ cephdeploy_ver)
    
    f = open('rpm_versions.txt', 'w')
    f.write('ceph rpm version is - '+ceph_ver+'\n')
    f.write('ceph-deploy rpm version is - '+cephdeploy_ver+'\n')
    cmd = 'lsb_release -a'
    rc,stdout,stderr = launch(cmd=cmd)
    f.write('Admin node details - \n'+stdout)
    f.close()
    

def getDefaultPools():
    cmd = 'ceph osd lspools'
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info("the default pools are "+stdout.strip())
    return str(stdout).strip()

def getMonStat():
    cmd = 'ceph mon stat'
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info("the mon stat is "+stdout.strip())
    return str(stdout).strip()

def getOSDStat(): 
    cmd = 'ceph osd stat' 
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info("the osd stat is "+stdout.strip())
    return str(stdout).strip()
 
def getquorum_status(): 
    cmd = 'ceph quorum_status' 
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info("the quorum_status is "+stdout.strip())
    return str(stdout).strip()


def getOSDtree(): 
    cmd = 'ceph osd tree' 
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info("the osd tree is \n"+stdout.strip())
    return str(stdout).strip()

