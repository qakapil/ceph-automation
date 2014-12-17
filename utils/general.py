import os, sys
from launch import launch
import logging
import zypperutils

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
    builds = stdout.strip().split('\n')
    build_version = builds[len(builds)-1]
    #build_version = stdout.strip().split('\n')[0]
    log.info('ISO build version is - Build'+build_version)
    return 'Build'+build_version


def mountISO(build_num, staging=True):
    mount_dir = '/suse'
    cmd = 'ssh %s sudo mkdir -p %s' % (os.environ["CLIENTNODE"], mount_dir)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)

    cmd = 'ssh %s sudo umount -f %s' % (os.environ["CLIENTNODE"], mount_dir)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
            log.warning("Error while executing the command '%s'. \
            Error message: '%s'" % (cmd, stderr))    

 
    cmd = 'ssh %s sudo mount loki:/real-home/ %s' % (os.environ["CLIENTNODE"], mount_dir)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
            log.warning("Error while executing the command '%s'. \
            Error message: '%s'" % (cmd, stderr))
    
    mount_dir = '/mounts/dist'
    cmd = 'ssh %s sudo mkdir -p %s' % (os.environ["CLIENTNODE"], mount_dir)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
            log.warning("Error while executing the command '%s'. \
            Error message: '%s'" % (cmd, stderr))

    cmd = 'ssh %s sudo umount -f %s' % (os.environ["CLIENTNODE"], mount_dir)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
            log.warning("Error while executing the command '%s'. \
            Error message: '%s'" % (cmd, stderr))

    cmd = 'ssh %s sudo mount dist.suse.de:/dist %s' % (os.environ["CLIENTNODE"], mount_dir)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
            log.warning("Error while executing the command '%s'. \
            Error message: '%s'" % (cmd, stderr))


    mount_dir = '/srv/www/htdocs/SLE12/'
    cmd = 'ssh %s sudo mkdir -p %s' % (os.environ["CLIENTNODE"], mount_dir)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
            log.warning("Error while executing the command '%s'. \
            Error message: '%s'" % (cmd, stderr))
    
    cmd = 'ssh %s sudo umount -f %s' % (os.environ["CLIENTNODE"], mount_dir)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
            log.warning("Error while executing the command '%s'. \
            Error message: '%s'" % (cmd, stderr))
    
                          
    if staging == False:
        cmd = 'ssh %s sudo mount -o loop /mounts/dist/ibs/Devel:/Storage:/1.0/images/iso/SUSE-Storage-1.0-DVD-x86_64-%s-Media1.iso %s' % (os.environ["CLIENTNODE"], build_num, mount_dir)
    else:
        cmd = 'ssh %s sudo mount -o loop /mounts/dist/ibs/Devel:/Storage:/1.0:/Staging/images/iso/SUSE-Storage-1.0-DVD-x86_64-%s-Media1.iso %s' % (os.environ["CLIENTNODE"], build_num, mount_dir)
    
    #cmd = 'ssh %s sudo mount -o loop /mounts/dist/ibs/SUSE:/SLE-12:/Update:/Products:/Cloud5/images/iso/SUSE-Storage-1.0-DVD-x86_64-%s-Media1.iso %s' % (os.environ["CLIENTNODE"], build_num, mount_dir)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
            log.warning("Error while executing the command '%s'. \
            Error message: '%s'" % (cmd, stderr))



                          
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



def printRPMVersionsISO(iso_build_num):
    ceph_ver = getCephExpVersionISO()
    log.info("The version of ceph is "+ ceph_ver)
    print ("The version of ceph is "+ ceph_ver)
    
    cephdeploy_ver = getCephDeployExpVersionISO()
    log.info("The version of cephdeploy is "+ cephdeploy_ver)
    print ("The version of cephdeploy is ' "+ cephdeploy_ver)
    
    f = open('iso_versions.txt', 'w')
    f.write('ISO Build is - '+iso_build_num+'\n')
    f.write('ceph version is - '+ceph_ver+'\n')
    f.write('ceph-deploy version is - '+cephdeploy_ver+'\n')
    cmd = 'ssh %s cat /etc/issue' % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    f.write('Client node details - \n'+stdout.split('Welcome to')[1])
    f.close()


def runXCDCHK(build_num):
    
    cmd = 'ssh %s ls /tmp/xcd-auto/SUSE-Storage-1.0/%s/'\
    % (os.environ["CLIENTNODE"], build_num)
    rc,stdout,stderr = launch(cmd=cmd)
    log.info('build_num value '+ str(build_num))
    log.info('build_num type '+ str(type(build_num)))
    if rc == 0:
        log.warning("/tmp/xcd-auto/SUSE-Storage-1.0 '%s' removing it" % (build_num))
        cmd = 'ssh %s sudo rm -rf /tmp/xcd-auto/SUSE-Storage-1.0/%s/'\
        % (os.environ["CLIENTNODE"], build_num)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            log.warning("Error while executing the command '%s'. \
            Error message: '%s'" % (cmd, stderr))
                          
                          
    cmd = 'ssh %s /suse/kukuk/bin/xcdchk -d /tmp/xcd-auto/ -p SUSE-Storage-1.0 \
    -b %s -i -S -s /mounts/dist/install/SLP/SLE-12-Server-LATEST/x86_64/DVD1/suse/setup/descr/packages.gz -a x86_64 \
    -n /srv/www/htdocs/SLE12/' % (os.environ["CLIENTNODE"], build_num)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    
    
    
    cmd = 'ssh %s ls /tmp/xcd-auto/SUSE-Storage-1.0/%s/x86_64/SATSOLVER.txt'\
    % (os.environ["CLIENTNODE"], build_num)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc == 0:
        cmd = 'scp %s:/tmp/xcd-auto/SUSE-Storage-1.0/%s/x86_64/SATSOLVER.txt .'\
        % (os.environ["CLIENTNODE"], build_num)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. \
                              Error message: '%s'" % (cmd, stderr)
    else:
        log.info("No SATSOLVER was generated")
        
        
    
    cmd = 'scp %s:/tmp/xcd-auto/SUSE-Storage-1.0/%s/x86_64/ChangeLog--%s.txt ChangeLog.txt'\
    % (os.environ["CLIENTNODE"], build_num, build_num)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    

def removeOldxcdFiles():
    cmd = "sudo rm SATSOLVER.txt ChangeLog.txt"
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.warning("Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr))
  
def installStartLighthttp(node):
    zypperutils.installPkg('lighttpd', node)
    cmd = 'ssh %s sudo /etc/init.d/lighttpd start' % (node)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.warning("Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr))






def verifycleanup(listNodes):
    for node in listNodes:
        cmd = "ssh %s df | awk '{print $6}'" % (node)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
        if stdout.find("ceph/osd") != -1:
            raise Exception, "OSD was not unmounted. df ouput - "+str(stdout)


        cmd = "ssh %s ls /var/lib/ceph/" % (node)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc == 0:
            raise Exception, "/var/lib/ceph dir still exists on node %s" % node
       
        cmd = "ssh %s ls /etc/ceph" % (node)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc == 0:
            raise Exception, "/etc/ceph dir still exists on node %s" % node 


def updateCephConf_NW(public_nw, cluster_nw):
    cmd = 'scp %s:ceph.conf .'% (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc == 0:
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. \
                              Error message: '%s'" % (cmd, stderr)

    f = file('ceph.conf','r')
    data = f.read()
    f.close()
    data = data[:len(data)-2]
    cluster_nw = 'cluster network = %s'%(cluster_nw)
    public_nw = 'public network = %s'%(public_nw)
    data = data+'\n'+cluster_nw+'\n'+public_nw+'\n'
    f = file('ceph.conf','w')
    f.write(data)
    f.close()

    cmd = 'scp ceph.conf %s:'% (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc == 0:
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. \
                              Error message: '%s'" % (cmd, stderr)
