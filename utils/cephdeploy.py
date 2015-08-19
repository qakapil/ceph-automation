from launch import launch
import general
import zypperutils
import logging, sys, os

log = logging.getLogger(__name__)

def declareInitialMons(listMons, keyserver=False):
    if len(listMons) < 1:
        log.error("initial mons list not provided in the yaml file")
        raise Exception, "initial mons list not provided in the yaml file"
    monlist = " ".join(listMons)
    suffix = ''
    if keyserver:
        suffix = '--dmcrypt-key-server ' + str(keyserver)
    cmd = 'ssh %s ceph-deploy new %s %s' % (os.environ["CLIENTNODE"], suffix, monlist)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)


def installNodes(listNodes):
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
    cmd = 'ssh %s ceph-deploy --overwrite-conf mon create-initial' % (os.environ["CLIENTNODE"])
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

def osdPrepare(listOSDs, dmcrypt=False):
    if len(listOSDs) < 1:
        log.error("OSDs list not provided in the yaml file")
        raise Exception, "OSDs list not provided in the yaml file"
    for osd in listOSDs:
        if dmcrypt:
            cmd = 'ssh %s ceph-deploy osd --dmcrypt prepare %s' % (os.environ["CLIENTNODE"], osd)
        else:
            cmd = 'ssh %s ceph-deploy osd prepare %s' % (os.environ["CLIENTNODE"], osd)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)

def osdActivate(listOSDs, dmcrypt=False):
    if len(listOSDs) < 1:
        log.error("OSDs list not provided in the yaml file")
        raise Exception, "OSDs list not provided in the yaml file"
    for osd in listOSDs:
        if dmcrypt:
            cmd = 'ssh %s ceph-deploy osd --dmcrypt activate %s' % (os.environ["CLIENTNODE"], osd)
        else:
            cmd = 'ssh %s ceph-deploy osd activate %s' % (os.environ["CLIENTNODE"], osd)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)


def PrepareActivateOSDs(listOSDs, dmcrypt=False):
    if len(listOSDs) < 1:
        log.error("OSDs list not provided in the yaml file")
        raise Exception, "OSDs list not provided in the yaml file"
    for osd in listOSDs:
        if dmcrypt:
            cmd = 'ssh %s ceph-deploy osd --dmcrypt prepare %s' % (os.environ["CLIENTNODE"], osd)
        else:
            cmd = 'ssh %s ceph-deploy osd prepare %s' % (os.environ["CLIENTNODE"], osd)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)

        if dmcrypt:
            cmd = 'ssh %s ceph-deploy osd --dmcrypt activate %s' % (os.environ["CLIENTNODE"], osd)
        else:
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
      

def cleanupNodes(listNodes, reponame, media2_repo=None):
    if len(listNodes) < 1:
        log.error("install nodes list not provided in the yaml file")
        raise Exception, "install nodes list not provided in the yaml file"
    allnodes = " ".join(listNodes)
    cmd = 'ssh %s ceph-deploy purge %s' % (os.environ["CLIENTNODE"], allnodes)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    cmd = 'ssh %s ceph-deploy purgedata %s' % (os.environ["CLIENTNODE"], allnodes)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    cmd = 'ssh %s ceph-deploy forgetkeys' % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    
    for node in listNodes:
        try:
            zypperutils.removeAllPkgsFromRepo(reponame, node)
        except Exception as e:
            log.warning("Error while removing packages...."+str(sys.exc_info()[1]))
        cmd = "ssh %s sudo zypper removerepo %s" % (node, reponame)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            log.warning("Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr))
        
        if media2_repo != None:
            try:
                zypperutils.removeAllPkgsFromRepo(media2_repo, node)
            except Exception as e:
                log.warning("Error while removing packages...."+str(sys.exc_info()[1]))
            cmd = "ssh %s sudo zypper removerepo %s" % (node, media2_repo)
            rc,stdout,stderr = launch(cmd=cmd)
            if rc != 0:
                log.warning("Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr))
        try:
            zypperutils.zypperRefresh(node)
        except Exception as e:
            log.warning("Error while removing ceph-deploy "+str(sys.exc_info()[1]))
    #verify the cleanup on each node
    general.verifycleanup(listNodes)
           
    
def getExpectedVersion(url):
    url = url+'noarch'
    cmd = 'ssh %s wget -q -O- %s | grep ceph-deploy | sed -e "s|.*ceph-deploy-\\(.*\\).noarch.rpm.*|\\1|"' \
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
