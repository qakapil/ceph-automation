from launch import launch
import general
import zypperutils
import logging, sys, os

log = logging.getLogger(__name__)

def declareInitialMons(listMons):
    if len(listMons) < 1:
        log.error("initial mons list not provided in the yaml file")
        raise Exception, "initial mons list not provided in the yaml file"
    monlist = " ".join(listMons)
    cmd = 'ssh %s ceph-deploy new %s' % (os.environ["CLIENTNODE"], monlist)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    
    
    
def installNodes(listNodes, repourl, gpgurl):
    if len(listNodes) < 1:
        log.error("install nodes list not provided in the yaml file")
        raise Exception, "install nodes list not provided in the yaml file"
    listNodes = " ".join(listNodes)
    #cmd = 'ceph-deploy install %s' % (listNodes)
    cmd = 'ssh %s ceph-deploy install --adjust-repos --repo-url %s --gpg-url %s \
    %s' % (os.environ["CLIENTNODE"], repourl, gpgurl, listNodes)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)



def installNodes_ISO(listNodes):
    if len(listNodes) < 1:
        log.error("install nodes list not provided in the yaml file")
        raise Exception, "install nodes list not provided in the yaml file"
    listNodes = " ".join(listNodes)
    #cmd = 'ceph-deploy install %s' % (listNodes)
    cmd = 'ssh %s ceph-deploy install %s' % (os.environ["CLIENTNODE"], listNodes)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    
    


def createInitialMons(listMons):
    if len(listMons) < 1:
        log.error("initial mons list not provided in the yaml file")
        raise Exception, "initial mons list not provided in the yaml file"
    cmd = 'ssh %s ceph-deploy mon create-initial' % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)


def osdZap(listOSDs):
    if len(listOSDs) < 1:
        log.error("OSDs list not provided in the yaml file")
        raise Exception, "OSDs list not provided in the yaml file"
    for osd in listOSDs:
        cmd = 'ssh %s ceph-deploy disk zap %s' % (os.environ["CLIENTNODE"], osd)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)

def osdPrepare(listOSDs):
    if len(listOSDs) < 1:
        log.error("OSDs list not provided in the yaml file")
        raise Exception, "OSDs list not provided in the yaml file"
    for osd in listOSDs:
        cmd = 'ssh %s ceph-deploy osd prepare %s' % (os.environ["CLIENTNODE"], osd)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)

def osdActivate(listOSDs):
    if len(listOSDs) < 1:
        log.error("OSDs list not provided in the yaml file")
        raise Exception, "OSDs list not provided in the yaml file"
    for osd in listOSDs:
        cmd = 'ssh %s ceph-deploy osd activate %s' % (os.environ["CLIENTNODE"], osd)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)


def PrepareActivateOSDs(listOSDs):
    if len(listOSDs) < 1:
        log.error("OSDs list not provided in the yaml file")
        raise Exception, "OSDs list not provided in the yaml file"
    for osd in listOSDs:
        cmd = 'ssh %s ceph-deploy osd prepare %s' % (os.environ["CLIENTNODE"], osd)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
        cmd = 'ssh %s ceph-deploy osd activate %s' % (os.environ["CLIENTNODE"], osd)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)

def CreateOSDs(listOSDs):   
    if len(listOSDs) < 1:
        log.error("OSDs list not provided in the yaml file")
        raise Exception, "OSDs list not provided in the yaml file"
    for osd in listOSDs:
        cmd = 'ssh %s ceph-deploy osd create %s' % (os.environ["CLIENTNODE"], osd)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
  
    
def addAdminNodes(listNodes):
    if len(listNodes) < 1:
        log.error("install nodes list not provided in the yaml file")
        raise Exception, "install nodes list not provided in the yaml file"
    strlistNodes = " ".join(listNodes)
    cmd = 'ssh %s ceph-deploy admin %s' % (os.environ["CLIENTNODE"], strlistNodes)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    
    for node in listNodes:
        cmd = 'ssh %s sudo chmod +r /etc/ceph/ceph.client.admin.keyring' % (node)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
      

def cleanupNodes(listNodes, reponame):
    if len(listNodes) < 1:
        log.error("install nodes list not provided in the yaml file")
        raise Exception, "install nodes list not provided in the yaml file"
    allnodes = " ".join(listNodes)
    cmd = 'ssh %s ceph-deploy purge %s' % (os.environ["CLIENTNODE"], allnodes)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.warning("Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr))
    cmd = 'ssh %s ceph-deploy purgedata %s' % (os.environ["CLIENTNODE"], allnodes)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.warning("Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr))
    cmd = 'ssh %s ceph-deploy forgetkeys' % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.warning("Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr))
    
    for node in listNodes:
        cmd = "ssh %s sudo zypper removerepo %s" % (node, reponame)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            log.warning("Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr))
        cmd = "ssh %s sudo zypper refresh" % (node)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            log.warning("Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr))
        try:
            zypperutils.removePkg('ceph-deploy', node)
        except Exception as e:
            log.warning("Error while removing ceph-deploy "+str(sys.exc_info()[0]))
        try:
            zypperutils.zypperRefresh(node)
        except Exception as e:
            log.warning("Error while removing ceph-deploy "+str(sys.exc_info()[0]))
    #verify the cleanup on each node
    general.verifycleanup(listNodes)
           
    
def getExpectedVersion(url):
    url = url+'src'
    cmd = 'ssh %s wget -q -O- %s | grep ceph-deploy | sed -e "s|.*ceph-deploy-\\(.*\\).src.rpm.*|\\1|"' \
     % (os.environ["CLIENTNODE"], url)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    cephdeploy_version = stdout.strip()
    log.info('CephDeploy expected version is - '+cephdeploy_version)
    return cephdeploy_version


def getActuaVersion():
    #cmd = 'ceph-deploy --version'
    cmd = 'ssh %s rpm -qa | grep ceph-deploy | sed -e "s|.*ceph-deploy-\\(.*\\)|\\1|"' % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    cephdeploy_version = stdout.strip()
    cephdeploy_version = cephdeploy_version.split("-")[0]
    log.info('CephDeploy actual version is - '+cephdeploy_version)
    return cephdeploy_version

def prepareInvalidOSD(listOSDs):
    node = listOSDs[0].split(":")[0]
    invaliddrive='sdz'  #assume sdz does not exist
    cmd = 'ssh %s ceph-deploy osd prepare %s:%s' % (os.environ["CLIENTNODE"], node, invaliddrive)
    rc,stdout,stderr = launch(cmd=cmd)
    return rc
    
    
    
        
