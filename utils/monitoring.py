from launch import launch
import logging
import ConfigParser

log = logging.getLogger(__name__)



def getCephHealth():
    cmd = 'ceph health'
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    log.info('Ceph health is - '+stdout)
    return stdout

def getFSID(workingdir):
    log.info('fetching fsid from ceph.conf in cephdeploy working dir')
    configParser = ConfigParser.RawConfigParser()
    configFilePath = workingdir+r'/ceph.conf'
    #configFilePath = r'ceph.conf'
    configParser.read(configFilePath)
    s = configParser.sections()
    print str(s)
    fsid = configParser.get('global','fsid')
    return fsid.strip()



def getCephStatus():
    cmd = 'ceph --status'
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    log.info('ceph status is - '+stdout)
    return stdout.strip()


    
def getExpectedVersion(url):
    url = url+'/src'
    cmd = 'wget -q -O- %s | grep ceph-0 | sed -e "s|.*ceph-\(.*\).src.rpm.*|\1|"' % (url)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    ceph_version = stdout.strip()
    log.info('Ceph expected version is - '+ceph_version)
    return ceph_version


def getActuaVersion():
    cmd = 'ceph --version'
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    ceph_version = stdout.strip()
    log.info('Ceph expected version is - '+ceph_version)
    return ceph_version
    
