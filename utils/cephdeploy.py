from launch import launch
import zypperutils
import logging


log = logging.getLogger(__name__)

def decalreInitialMons(listMons, strWorkingdir):
    if len(listMons) < 1:
        log.error("initial mons list not provided in the yaml file")
        raise Exception, "initial mons list not provided in the yaml file"
    monlist = " ".join(listMons)
    cmd = 'ceph-deploy new %s' % (monlist)
    rc,stdout,stderr = launch(cmd=cmd,cwd=strWorkingdir)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    
    
    
def installNodes(listNodes, strWorkingdir):
    if len(listNodes) < 1:
        log.error("install nodes list not provided in the yaml file")
        raise Exception, "install nodes list not provided in the yaml file"
    listNodes = " ".join(listNodes)
    cmd = 'ceph-deploy install %s' % (listNodes)
    rc,stdout,stderr = launch(cmd=cmd,cwd=strWorkingdir)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)



def createInitialMons(listMons, strWorkingdir):
    if len(listMons) < 1:
        log.error("initial mons list not provided in the yaml file")
        raise Exception, "initial mons list not provided in the yaml file"
    cmd = 'ceph-deploy mon create-initial'
    rc,stdout,stderr = launch(cmd=cmd,cwd=strWorkingdir)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)



def PrepareActivateOSDs(listOSDs, strWorkingdir):
    if len(listOSDs) < 1:
        log.error("OSDs list not provided in the yaml file")
        raise Exception, "OSDs list not provided in the yaml file"
    for osd in listOSDs:
        cmd = 'ceph-deploy osd prepare %s' % (osd)
        rc,stdout,stderr = launch(cmd=cmd,cwd=strWorkingdir)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
        cmd = 'ceph-deploy osd activate %s' % (osd)
        rc,stdout,stderr = launch(cmd=cmd,cwd=strWorkingdir)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)

def CreateOSDs(listOSDs, strWorkingdir):   
    if len(listOSDs) < 1:
        log.error("OSDs list not provided in the yaml file")
        raise Exception, "OSDs list not provided in the yaml file"
    for osd in listOSDs:
        cmd = 'ceph-deploy osd create %s' % (osd)
        rc,stdout,stderr = launch(cmd=cmd,cwd=strWorkingdir)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
  
    
def addAdminNodes(listNodes, strWorkingdir):
    if len(listNodes) < 1:
        log.error("install nodes list not provided in the yaml file")
        raise Exception, "install nodes list not provided in the yaml file"
    listNodes = " ".join(listNodes)
    cmd = 'ceph-deploy admin %s' % (listNodes)
    rc,stdout,stderr = launch(cmd=cmd,cwd=strWorkingdir)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
      

def cleanupNodes(listNodes, reponame, strWorkingdir):
    if len(listNodes) < 1:
        log.error("install nodes list not provided in the yaml file")
        raise Exception, "install nodes list not provided in the yaml file"
    allnodes = " ".join(listNodes)
    cmd = 'ceph-deploy purge %s' % (allnodes)
    rc,stdout,stderr = launch(cmd=cmd,cwd=strWorkingdir)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    cmd = 'ceph-deploy purgedata %s' % (allnodes)
    rc,stdout,stderr = launch(cmd=cmd,cwd=strWorkingdir)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    cmd = 'ceph-deploy forgetkeys'
    rc,stdout,stderr = launch(cmd=cmd,cwd=strWorkingdir)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    
    for node in listNodes:
        cmd = "ssh %s sudo zypper removerepo %s" % (node, reponame)
        rc,stdout,stderr = launch(cmd=cmd,cwd=strWorkingdir)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
        cmd = "ssh %s sudo zypper refresh" % (node)
        rc,stdout,stderr = launch(cmd=cmd,cwd=strWorkingdir)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    zypperutils.removePkg('ceph-deploy')
    zypperutils.removeRepo('ceph')
    
    
    
        