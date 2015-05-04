from launch import launch
import logging
import ConfigParser
import cephdeploy
import re, os

log = logging.getLogger(__name__)



def getCephHealth():
    cmd = 'ssh %s ceph health' % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    log.info('Ceph health is - '+stdout)
    return stdout

def getFSID():
    cmd = 'ssh %s ceph-conf --lookup fsid' % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    fsid = stdout.strip()
    log.info('ceph fsid is - '+fsid)
    return fsid




def getCephStatus():
    cmd = 'ssh %s ceph --status' % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    log.info('ceph status is - '+stdout)
    return stdout.strip()


    
def getExpectedVersion(url):
    url = url+'src'
    cmd = 'ssh %s wget -q -O- %s | grep ceph-0 | sed -e "s|.*ceph-\\(.*\\).src.rpm.*|\\1|"' % (os.environ["CLIENTNODE"], url)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    ceph_version = stdout.strip()
    log.info('Ceph expected version is - '+ceph_version)
    return ceph_version


def getActuaVersion():
    cmd = 'ssh %s ceph --version' % (os.environ["CLIENTNODE"])
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
    log.info("The expected rpm version of ceph is "+ ceph_ver)

    cephdeploy_ver = cephdeploy.getExpectedVersion(url)
    log.info("The expected rpm version of ceph-deploy is "+ cephdeploy_ver)

    f = open('rpm_versions.txt', 'w')
    f.write('ceph rpm version is - '+ceph_ver+'\n')
    f.write('ceph-deploy rpm version is - '+cephdeploy_ver+'\n')
    cmd = 'ssh %s cat /etc/issue' % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    f.write('Client node details - \n'+stdout.split('Welcome to')[1])
    f.close()
    

def getDefaultPools():
    cmd = 'ssh %s ceph osd lspools' % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info("the default pools are "+stdout.strip())
    return str(stdout).strip()

def getMonStat():
    cmd = 'ssh %s ceph mon stat' % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info("the mon stat is "+stdout.strip())
    return str(stdout).strip()

def getOSDStat(): 
    cmd = 'ssh %s ceph osd stat' % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info("the osd stat is "+stdout.strip())
    return str(stdout).strip()
 
def getquorum_status(): 
    cmd = 'ssh %s ceph quorum_status' % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info("the quorum_status is "+stdout.strip())
    return str(stdout).strip()


def getOSDtree(): 
    cmd = 'ssh %s ceph osd tree' % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info("the osd tree is \n"+stdout.strip())
    return str(stdout).strip()

def getTotalPGs(): 
    cmd = "ssh %s ceph pg stat| awk '{print $2;}'" % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info("the total PGS \n"+stdout.strip())
    return str(stdout).strip()

