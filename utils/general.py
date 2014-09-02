import os, sys
from launch import launch
import logging

log = logging.getLogger(__name__)

def createDirOLD(dirPath):
    if not os.path.isdir(dirPath):
        try:
            os.mkdir(dirPath)
        except  Exception as e:
            log.error("Error while creating the dir: "+dirPath, sys.exc_info()[0])
            raise Exception, e
    else:
        log.info("the directory '%S' already exists")
        

def createDir(dirPath, machineName=None):
    if machineName == None:
        cmd1 = "ls -l %s" % (dirPath)
        if 'var' in dirPath.split('/'):
            cmd2 = "sudo mkdir -p %s" % (dirPath)
        else:
            cmd2 = "mkdir -p %s" % (dirPath)
    else:
        cmd1 = "ssh %s ls -l %s" % (machineName, dirPath)
        if 'var' in dirPath.split('/'):
            cmd2 = "ssh %s sudo mkdir -p %s" % (machineName, dirPath)
        else:
            cmd2 = "ssh %s mkdir -p %s" % (machineName, dirPath)
        
        
    cmd = cmd1
    rc,stdout,stderr = launch(cmd=cmd)
    if rc == 0 and stderr.strip() == "":
        log.info("directory %s is already present, not creating " % (dirPath))
        return
    cmd = cmd2
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.error("error while creating the directory %s " % (dirPath))
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)


def removerpm(rpmname):
    cmd = "sudo rpm -e %s" % (rpmname)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.error("error while creating the directory %s " % (rpmname))
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    
    
def getISOBuildNum(url):
    url = url.strip()
    cmd = 'wget -q -O- %s | grep Media1 | sed -e "s|.*Build\\(.*\\)-Media1.*|\\1|"' % (url)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    build_version = stdout.strip()
    log.info('ISO build version is - Build'+build_version)
    return 'Build'+build_version


def mountISO(build_num):
    mount_dir = '/srv/www/htdocs/SLE12/'
    cmd = 'ssh %s sudo mkdir -p %s' % (os.environ["CLIENTNODE"], mount_dir)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    
    cmd = 'ssh %s sudo umount %s' % (os.environ["CLIENTNODE"], mount_dir)
    rc,stdout,stderr = launch(cmd=cmd)
    
                          
    cmd = 'ssh %s sudo mount -o loop /mounts/dist/ibs/Devel:/Storage:/1.0:/Staging/images/iso/SUSE-Storage-1.0-DVD-x86_64-%s-Media1.iso %s' % (os.environ["CLIENTNODE"], build_num, mount_dir)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
                          
def getCephDeployExpVersionISO():
    cmd = 'ssh %s ls /srv/www/htdocs/SLE12/suse/noarch/ | grep ceph-deploy'\
    % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    cephdeploy_version = stdout.strip()
    log.info('Ceph expected version is - '+cephdeploy_version)
    return cephdeploy_version


def getCephExpVersionISO():
    cmd = 'ssh %s ls /srv/www/htdocs/SLE12/suse/x86_64/ | grep ^ceph-0'\
    % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    ceph_version = stdout.strip()
    log.info('Ceph expected version is - '+ceph_version)
    return ceph_version



def printRPMVersionsISO():
    ceph_ver = getCephExpVersionISO()
    log.info("The version of ceph is "+ ceph_ver)
    print ("The version of ceph is "+ ceph_ver)
    
    cephdeploy_ver = getCephDeployExpVersionISO()
    log.info("The version of cephdeploy is "+ cephdeploy_ver)
    print ("The version of cephdeploy is ' "+ cephdeploy_ver)
    
    f = open('iso_versions.txt', 'w')
    f.write('ceph version is - '+ceph_ver+'\n')
    f.write('ceph-deploy version is - '+cephdeploy_ver+'\n')
    cmd = 'ssh %s cat /etc/issue' % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    f.write('Client node details - \n'+stdout.split('Welcome to')[1])
    f.close()


def runXCDCHK(build_num):
    cmd = 'ssh %s /suse/kukuk/bin/xcdchk -d /tmp/xcd-auto/ -p SUSE-Storage-1.0 \
    -b %s -i -S -s /mounts/dist/install/SLP/SLE-12-Server-RC2/x86_64/DVD1/suse/setup/descr/packages.gz -a x86_64 \
    -n /srv/www/htdocs/SLE12/' % (os.environ["CLIENTNODE"], build_num)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)

    cmd = 'scp %s:/tmp/xcd-auto/SUSE-Storage-1.0/%s/x86_64/SATSOLVER.txt .'\
    % (os.environ["CLIENTNODE"], build_num)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    
    cmd = 'scp %s:/tmp/xcd-auto/SUSE-Storage-1.0/%s/x86_64/ChangeLog--%s.txt ChangeLog.txt'\
    % (os.environ["CLIENTNODE"], build_num, build_num)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    

   