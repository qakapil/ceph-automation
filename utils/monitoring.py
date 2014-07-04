from launch import launch
import logging
import ConfigParser

log = logging.getLogger(__name__)



def getCephHealth():
    cmd = 'ceph health'
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    log.info('Ceph health is %s - ')%(stdout)
    return stdout

def getFSID():
    log.info('fetching fsid from ceph.conf in cephdeploy working dir')
    configParser = ConfigParser.RawConfigParser()
    configFilePath = r'ceph.conf'
    configParser.read(configFilePath)
    fsid = configParser.get('global','fsid')
    return fsid.strip()



def getCephStatus():
    cmd = 'ceph --status'
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    log.info('Ceph status is %s - ')%(stdout)
    return stdout.strip()


    
def getExpectedVersion(url):
    url = url+'/src'
    cmd = 'wget -q -O- %s | grep ceph-0 | sed -e "s|.*ceph-\(.*\).src.rpm.*|\1|"' % (url)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    ceph_version = stdout.strip()
    log.info('Ceph expected version is %s - ')%(ceph_version)
    return ceph_version


def getActuaVersion():
    cmd = 'ceph --version'
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    ceph_version = stdout.strip()
    log.info('Ceph expected version is %s - ')%(ceph_version)
    return ceph_version
    
