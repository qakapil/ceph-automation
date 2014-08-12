from launch import launch
import logging
import ConfigParser
import cephdeploy
import re

log = logging.getLogger(__name__)

# this code is forked as most methods must take a node


def getCephHealth(node):
    cmd = 'ceph health'
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    log.info('Ceph health is - '+stdout)
    return stdout

def getFSID(node):
    # forked as ceph local node is not part of cluster and must run on node
    cmd = 'ssh %s sudo ceph-conf --lookup fsid' % (node)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    fsid = stdout.strip()
    log.info('ceph fsid is - '+fsid)
    return fsid

def getCephStatus(node):
    # forked as ceph local node is not part of cluster and must run on node
    cmd = 'ssh %s sudo ceph --status' % (node)
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


def getActuaVersion(node):
    cmd = 'ssh %s sudo ceph --version' % (node)
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
    

def getDefaultPools(node):
    cmd = 'ssh %s sudo ceph osd lspools' % (node)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info("the default pools are "+stdout.strip())
    return str(stdout).strip()

def getMonStat(node):
    cmd = 'ssh %s sudo ceph mon stat' % (node)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info("the mon stat is "+stdout.strip())
    return str(stdout).strip()

def getOSDStat(node): 
    cmd = 'ssh %s sudo ceph osd stat'  % (node)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info("the osd stat is "+stdout.strip())
    return str(stdout).strip()
 
def getquorum_status(node): 
    cmd = 'ssh %s sudo ceph quorum_status'  % (node)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info("the quorum_status is "+stdout.strip())
    return str(stdout).strip()


def getOSDtree(node): 
    cmd = 'ssh %s sudo ceph osd tree' % (node)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info("the osd tree is \n"+stdout.strip())
    return str(stdout).strip()

def getTotalPGs(node): 
    cmd = "ssh %s sudo ceph pg stat| awk '{print $2;}'" % (node)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info("the total PGS \n"+stdout.strip())
    return str(stdout).strip()

