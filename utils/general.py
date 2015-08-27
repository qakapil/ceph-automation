import os, sys
from launch import launch
import logging
import zypperutils
import time
import json
import ast
import general
log = logging.getLogger(__name__)


def convert_to_structure(stdout):
    return ast.literal_eval(stdout)


def eval_returns(cmd):
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    #log.debug(stdout)
    return stdout, stderr


def exe_command(cmd):
    rc, stdout, stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)


def hand_error_message(cmd):
    rc, stdout, stderr = launch(cmd=cmd)
    return stdout, stderr


def createDirOLD(dirPath):
    if not os.path.isdir(dirPath):
        try:
            os.mkdir(dirPath)
        except Exception as e:
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
    cmd = 'wget -q -O- %s | grep Media1 | grep Storage | grep -v -i  Internal \
    | sed -e "s|.*Build\\(.*\\)-Media1.*|\\1|"' % (url)
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

 
    cmd = 'ssh %s sudo mount loki.suse.de:/real-home/ %s' % (os.environ["CLIENTNODE"], mount_dir)
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
        cmd = 'ssh %s sudo mount -o loop /mounts/dist/ibs/Devel:/Storage:/1.0/images/iso/SUSE-Enterprise-Storage-1.0-DVD-x86_64-%s-Media1.iso %s' % (os.environ["CLIENTNODE"], build_num, mount_dir)
    else:
        cmd = 'ssh %s sudo mount -o loop /mounts/dist/ibs/Devel:/Storage:/1.0:/Staging/images/iso/SUSE-Enterprise-Storage-1.0-DVD-x86_64-%s-Media1.iso %s' % (os.environ["CLIENTNODE"], build_num, mount_dir)
    
    #cmd = 'ssh %s sudo mount -o loop /mounts/dist/ibs/SUSE:/SLE-12:/Update:/Products:/Cloud5/images/iso/SUSE-Storage-1.0-DVD-x86_64-%s-Media1.iso %s' % (os.environ["CLIENTNODE"], build_num, mount_dir)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
            log.warning("Error while executing the command '%s'. \
            Error message: '%s'" % (cmd, stderr))



                          
def getCephDeployExpVersionISO(media=None):
    if media != None:
        cmd = 'ssh %s ls %s/suse/noarch/ | grep ceph-deploy'\
    % (os.environ["CLIENTNODE"], media)
    else:
        cmd = 'ssh %s ls /srv/www/htdocs/SLE12/suse/noarch/ | grep ceph-deploy'\
    % (os.environ["CLIENTNODE"])

    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    cephdeploy_version = stdout.strip()
    log.info('Ceph expected version is - '+cephdeploy_version)
    return cephdeploy_version


def getCephExpVersionISO(media=None):
    if media != None:
        cmd = 'ssh %s ls %s/suse/x86_64/ | grep ^ceph-0'\
    % (os.environ["CLIENTNODE"], media)
    else:
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


def runXCDCHK(build_num, media_path=None, media='Media1'):
    
    cmd = 'ssh %s ls /tmp/xcd-auto/SUSE-Storage-1.0/%s/'\
    % (os.environ["CLIENTNODE"], build_num)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc == 0:
        log.warning("/tmp/xcd-auto/SUSE-Storage-1.0 '%s' removing it" % (build_num))
        cmd = 'ssh %s sudo rm -rf /tmp/xcd-auto/SUSE-Storage-1.0/%s/'\
        % (os.environ["CLIENTNODE"], build_num)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            log.warning("Error while executing the command '%s'. \
            Error message: '%s'" % (cmd, stderr))
                          
    if (media_path==None):
        cmd = 'ssh %s /suse/kukuk/bin/xcdchk -d /tmp/xcd-auto/ -p SUSE-Storage-1.0 \
    -b %s -i -S -s /mounts/dist/install/SLP/SLE-12-Server-LATEST/x86_64/DVD1/suse/setup/descr/packages.gz -a x86_64 \
    -n /srv/www/htdocs/SLE12/' % (os.environ["CLIENTNODE"], build_num)
    else:
        cmd = 'ssh %s /suse/kukuk/bin/xcdchk -d /tmp/xcd-auto/ -p SUSE-Storage-1.0 \
    -b %s -i -S -s /mounts/dist/install/SLP/SLE-12-Server-LATEST/x86_64/DVD1/suse/setup/descr/packages.gz -a x86_64 \
    -n %s' % (os.environ["CLIENTNODE"], build_num, media_path)

    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    
    
    
    cmd = 'ssh %s ls /tmp/xcd-auto/SUSE-Storage-1.0/%s/x86_64/SATSOLVER.txt'\
    % (os.environ["CLIENTNODE"], build_num)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc == 0:
        cmd = 'scp %s:/tmp/xcd-auto/SUSE-Storage-1.0/%s/x86_64/SATSOLVER.txt SATSOLVER-%s.txt'\
        % (os.environ["CLIENTNODE"], build_num, media)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. \
                              Error message: '%s'" % (cmd, stderr)
    else:
        log.info("No SATSOLVER was generated")



    cmd = 'ssh %s ls /tmp/xcd-auto/SUSE-Storage-1.0/%s/x86_64/MISSING-SRPM.txt'\
    % (os.environ["CLIENTNODE"], build_num)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc == 0:
        cmd = 'scp %s:/tmp/xcd-auto/SUSE-Storage-1.0/%s/x86_64/MISSING-SRPM.txt MISSING-SRPM-%s.txt'\
        % (os.environ["CLIENTNODE"], build_num, media)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. \
                              Error message: '%s'" % (cmd, stderr)
    else:
        log.info("No MISSING-SRPM was generated")
        
        
    
    cmd = 'scp %s:/tmp/xcd-auto/SUSE-Storage-1.0/%s/x86_64/ChangeLog--%s.txt ChangeLog-%s.txt'\
    % (os.environ["CLIENTNODE"], build_num, build_num, media)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    

def removeOldxcdFiles():
    cmd = "sudo rm SATSOLVER* ChangeLog* MISSING-SRPM*"
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


def perNodeCleanUp(listNodes, reponame):
    diff_pkgs = ['python-cephfs', 'python-rbd', 'python-rados']
    for node in listNodes:
        try:
            zypperutils.removeAllPkgsFromRepo(reponame, node)
        except Exception as e:
            log.warning("Error while removing packages...."+str(sys.exc_info()[1]))
        for pkg in diff_pkgs:
            try:
                zypperutils.removePkg(pkg, node)
            except:
                log.warning("Error while removing pkg %s on node %s" % (pkg, node))

        cmd = "ssh %s df | awk '{print $6}'" % (node)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)

        mounts = stdout.split("\n")
        for mount in mounts:
            if mount.strip().find("ceph/osd") != -1:
                log.warning("Unmounting: %s - %s" % (node, mount))
                cmd = "ssh %s sudo umount -lfr %s" % (node, mount)
                for i in range(5):
                    rc,stdout,stderr = launch(cmd=cmd)
                    if rc == 0:
                        break
                    time.sleep(3)
                assert(rc == 0), "could not umount %s on %s error %s %s " % (mount,node,stdout,stderr)

        cmd = "ssh %s 'if test -d /etc/ceph; then sudo rm -rf /etc/ceph; fi'" % (node)
        rc,stdout,stderr = launch(cmd=cmd)
        assert(rc == 0), stderr
        cmd = "ssh %s 'if test -d /var/lib/ceph; then sudo rm -rf /var/lib/ceph; fi'" % (node)
        rc,stdout,stderr = launch(cmd=cmd)
        assert(rc == 0), stderr
        cmd = "ssh %s 'if test -d /var/run/ceph; then sudo rm -rf /var/run/ceph; fi'" % (node)
        rc,stdout,stderr = launch(cmd=cmd)
        assert(rc == 0), stderr
        cmd = "ssh %s 'rm ceph*'" % (node)
        rc,stdout,stderr = launch(cmd=cmd)

    verifycleanup(listNodes)
    zypperDUPReboot(listNodes, reponame)




def zypperDUPReboot(listNodes, reponame):
    for node in listNodes:
        zypperutils.zypperDup(node, reponame)
        cmd = "ssh root@%s sudo reboot" % (node)
        rc, stdout, stderr = launch(cmd=cmd)
        assert(rc == 255), stderr
    time.sleep(10)
    reboot_nodes = list(listNodes)

    counter = 0
    while len(reboot_nodes) > 0:
        for node in reboot_nodes:
            log.info("pinging "+ node)
            response = os.system("ping -c 4 " + node)
            if response == 0:
                log.info("ping was successfull")
                reboot_nodes.remove(node)
            if len(reboot_nodes) == 0:
                log.info("all the nodes rebooted successfully")
                break
            counter += 1
            if counter > 120:
                log.info("All nodes did not reboot after 30 mins ")
                raise Exception, "Following nodes did not reboot after 30 mins "\
                + str(reboot_nodes)
            log.info("still waiting for nodes - "+str(reboot_nodes))
            time.sleep(5)
    exp_str = 'No processes using deleted files found'
    for node in listNodes:
        cmd = "ssh %s sudo zypper ps" % (node)
        rc, stdout, stderr = launch(cmd=cmd)
        assert(rc == 0), stderr
        assert(exp_str in stdout.strip()), "processes were found running deleted files "+ stdout




def removeOldRepos(listNodes, listRepos):
    for node in listNodes:
        for repo in listRepos:
            isRepo = zypperutils.isRepoPresent(repo, node)
            if isRepo:
                zypperutils.removeAllPkgsFromRepo(repo, node)
                zypperutils.removeRepo(repo, node)


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


def updateCephConf_dmcrypt(dmcrypt_type, key_server=None, service_type=None):
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
    dmcrypt_type = 'osd_dmcrypt_type = %s'%(dmcrypt_type)
    if service_type:
        service_type = 'key_store_service = %s'%(service_type)
        key_server = 'dmcrypt_key_server = %s'%(key_server)
        data = data + '\n' + dmcrypt_type + '\n' + key_server + '\n' + service_type + '\n'
    else:
        data = data+'\n'+dmcrypt_type+'\n'
    f = file('ceph.conf','w')
    f.write(data)
    f.close()

    cmd = 'scp ceph.conf %s:' % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc == 0:
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. \
                              Error message: '%s'" % (cmd, stderr)


def downloadISOAddRepo(url, media, reponame, node, iso_name=None, iso_internal=False):
    build_version=iso_name
    url = url.strip()
    uname = os.environ.get("WGET_UNAME")
    passwd = os.environ.get("WGET_PASS")
    if iso_name == None:
        if (uname or passwd) ==  None:
            if iso_internal:
                cmd = 'ssh %s wget -q -O- %s | grep \'Storage.*Media.\' \
                | grep -i  Internal | sed -e "s|.*SUSE-\\(.*\\)-Media.*|\\1|"' % (node, url)
            else:
                cmd = 'ssh %s wget -q -O- %s | grep \'Storage.*Media.\' \
                | grep -v -i  Internal | sed -e "s|.*SUSE-\\(.*\\)-Media.*|\\1|"' % (node, url)
           
        else:
            cmd = 'ssh %s wget --http-user=%s --http-password=%s -q -O- %s | grep \'Storage.*Media\' \
            | grep -v -i  Internal | sed -e "s|.*SUSE-\\(.*\\)-Media.*|\\1|"' % (node, uname, passwd, url)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. \
                              Error message: '%s'" % (cmd, stderr)
        builds = stdout.strip().split('\n')
        build_version = builds[len(builds)-1]
        iso_name = 'SUSE-'+build_version+'-'+media+'.iso'

    log.info('ISO name  is - '+iso_name)
    
    iso_path = '/tmp/%s' % (iso_name)
    log.info('ISO path  is - '+iso_path)

    #cmd = 'ssh %s rm /tmp/*iso' %(node)
    #rc,stdout,stderr = launch(cmd=cmd)

    cmd = 'ssh %s ls %s' %(node, iso_path)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc == 0:
        log.info("old iso found. Deleting...")
        cmd = 'ssh %s sudo rm %s' %(node, iso_path)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. \
            Error message: '%s'" % (cmd, stderr)

    if (uname or passwd) ==  None:
        cmd = 'ssh %s wget %s/%s -P /tmp' %(node, url, iso_name)
    else:
       cmd = 'ssh %s wget --http-user=%s --http-password=%s %s/%s -P \
       /tmp' %(node, uname, passwd, url, iso_name)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)

    iso_uri = 'iso:///?iso=%s'% (iso_path)
    log.info('ISO uri  is - '+iso_uri)

    zypperutils.addRepo(reponame, iso_uri, node)
    return build_version


def mount_extISO(iso_path, mount_dir):
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

    cmd = 'ssh %s sudo mount -o loop %s %s' % (os.environ["CLIENTNODE"], iso_path, mount_dir)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr) 

    #also mount the /suse dir to run xcdchk from
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
    
    cmd = 'ssh %s sudo mount loki.suse.de:/real-home/ %s' % (os.environ["CLIENTNODE"], mount_dir)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
            log.warning("Error while executing the command '%s'. \
            Error message: '%s'" % (cmd, stderr))
    
    cmd = 'ssh %s ls \~kukuk' % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.warning("~kukuk not present. Creating...")
        cmd = 'ssh %s mkdir \~kukuk/ && ssh %s ln -s /suse/kukuk/bin/ \~kukuk/' % (os.environ["CLIENTNODE"],os.environ["CLIENTNODE"])
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. \
                  Error message: '%s'" % (cmd, stderr)


def printISOurl(iso_name, url):
    f = open('iso_versions.txt', 'w')
    f.write('ISO URL is - '+url+'\n')
    f.write('ISO build is  - '+iso_name+'\n')
    cmd = 'ssh %s cat /etc/issue' % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    f.write('Client node details - \n'+stdout.split('Welcome to')[1])
    f.close()


def runInstallCheck(node, baserepo, targetrepo, baserepo2=None):
    if baserepo2:
        cmd = 'ssh %s installcheck x86_64  --withobsoletes /var/cache/zypp/solv/%s/solv --nocheck /var/cache/zypp/solv/%s/solv /var/cache/zypp/solv/%s/solv' % (node, targetrepo, baserepo, baserepo2)
    else:
        cmd = 'ssh %s installcheck x86_64  --withobsoletes /var/cache/zypp/solv/%s/solv --nocheck /var/cache/zypp/solv/%s/solv' % (node, targetrepo, baserepo)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "InstallCheck Unsuccessfull. Error executing command '%s'. \
                  \nError message: \n '%s' \n '%s' " % (cmd, stdout, stderr)
    log.info('install check for repo %s against base repo %s was successfull' % (targetrepo, baserepo))


def findDupPackages(node, baserepo, targetrepo):
    cmd = "ssh %s zypper se -r %s | grep -v srcpackage | awk '{print $2}'" % (node, baserepo)
    rc,stdout,stderr = launch(cmd=cmd)
    assert(rc == 0), stderr
    list_baserepo = stdout.split("\n")[2:]
    list_baserepo = filter(lambda a: a != '', list_baserepo)
    list_baserepo = filter(lambda a: a != '|', list_baserepo)
    
    cmd = "ssh %s zypper se -r %s | grep -v srcpackage | awk '{print $2}'" % (node, targetrepo)
    rc,stdout,stderr = launch(cmd=cmd)
    assert(rc == 0), stderr
    list_targetrepo = stdout.split("\n")[2:]
    list_targetrepo = filter(lambda a: a != '', list_targetrepo)
    list_targetrepo = filter(lambda a: a != '|', list_targetrepo)

    assert(len(set(list_baserepo) & set(list_targetrepo)) == 0), "duplicate packages found "+str(set(list_baserepo) & set(list_targetrepo))


def runfioJobs(LE, **fio_dict):
    try:
        cmd = "ssh {node} rbd create {rbd_img_name} --size {size}".format(**fio_dict)
        rc,stdout,stderr = launch(cmd=cmd)
        assert(rc == 0), "failed to create image {rbd_img_name} on node {node}".format(**fio_dict)+"\n"+stderr
        cmd = "ssh {node} rm -rf perfjobs; ssh {node} mkdir -p perfjobs/fiojobs/logs".format(**fio_dict)
        rc,stdout,stderr = launch(cmd=cmd)
        cmd = "scp perfjobs/fio_template.fio {node}:perfjobs/fiojobs".format(**fio_dict)
        rc,stdout,stderr = launch(cmd=cmd)
        assert(rc == 0), stderr
        cmd = "ssh {node} IODEPTH={iodepth} RBDNAME={rbd_img_name} RW={rw} BLOCKSIZE={bs} \
RUNTIME={runtime} NUMJOBS={numjobs} fio perfjobs/fiojobs/fio_template.fio".format(**fio_dict)
        log.info("starting fio test on node {node}".format(**fio_dict))
        rc,stdout,stderr = launch(cmd=cmd)
        assert(rc == 0), "fio test failed on node {node}".format(**fio_dict)+"\n"+stderr
        node = "{node}".format(**fio_dict)
        cmd = 'echo "%s" > %s_results.log && scp %s_results.log %s:perfjobs/fiojobs/logs/ && rm %s_results.log' % (str(stdout),node,node,node,node)
        rc,stdout,stderr = launch(cmd=cmd)
        assert(rc == 0), stderr
        '''
        log.info("generating graphs using gio2gnuplot")
        cmd = "ssh %s 'cd perfjobs/fiojobs/logs && fio2gnuplot -p '*_bw*' -g'" % (node)
        rc,stdout,stderr = launch(cmd=cmd)
        assert(rc == 0), stderr
        cmd = "ssh %s 'cd perfjobs/fiojobs/logs && fio2gnuplot -p '*_iops*' -g'" % (node)
        rc,stdout,stderr = launch(cmd=cmd)
        assert(rc == 0), stderr
        '''
    except:
        LE.excList.append(sys.exc_info()[1])
        raise sys.exc_info()[0], sys.exc_info()[1]

    
    
def installPkgFromurl(node, url):
    cmd = "ssh %s sudo rpm -i %s" % (node, url)
    rc,stdout,stderr = launch(cmd=cmd)
    assert(rc == 0), "failed to install package %s on node %s" % (url, node) + "\n"+stderr



def storeClusterInfo(wdir,before_run=False):
    filename = "afterrun.log"
    if before_run:
        cmd = "rm -rf %s; mkdir %s" % (wdir, wdir)
        rc,stdout,stderr = launch(cmd=cmd)
        filename = "beforerun.log"

    filepath = "%s/%s" % (wdir, filename)

    cmd = "ssh %s ceph -s &>> %s;echo $'\n\n' &>> %s" % (os.environ["CLIENTNODE"], filepath, filepath)
    rc,stdout,stderr = launch(cmd=cmd)
    assert(rc == 0), stderr

    cmd = "ssh %s rados df &>> %s;echo $'\n\n' &>> %s" % (os.environ["CLIENTNODE"], filepath, filepath)
    rc,stdout,stderr = launch(cmd=cmd)
    assert(rc == 0), stderr

    cmd = "ssh %s ceph mon_status &>> %s;echo $'\n\n' &>> %s" % (os.environ["CLIENTNODE"], filepath, filepath)
    rc,stdout,stderr = launch(cmd=cmd)
    assert(rc == 0), stderr

    cmd = "ssh %s ceph osd tree &>> %s;echo $'\n\n' &>> %s" % (os.environ["CLIENTNODE"], filepath, filepath)
    rc,stdout,stderr = launch(cmd=cmd)
    assert(rc == 0), stderr

    cmd = "ssh %s ceph osd crush dump &>> %s;echo $'\n\n' &>> %s" % (os.environ["CLIENTNODE"], filepath, filepath)
    rc,stdout,stderr = launch(cmd=cmd)
    assert(rc == 0), stderr

    cmd = "scp %s:/etc/ceph/ceph.conf %s" % (os.environ["CLIENTNODE"], wdir)
    rc,stdout,stderr = launch(cmd=cmd)
    assert(rc == 0), stderr



def storeCephStatus(wdir,maxtime):
    filename = "runtime.log"
    filepath = "%s/%s" % (wdir, filename)
    delay = 60
    count = maxtime/delay
    for i in range(count):
        cmd = "ssh %s ceph -s &>> %s;echo $'\n\n' &>> %s" % (os.environ["CLIENTNODE"], filepath, filepath)
        rc,stdout,stderr = launch(cmd=cmd)
        assert(rc == 0), stderr

        cmd = "ssh %s rados df &>> %s;echo $'\n\n' &>> %s" % (os.environ["CLIENTNODE"], filepath, filepath)
        rc,stdout,stderr = launch(cmd=cmd)
        assert(rc == 0), stderr

        time.sleep(delay)

        


def scpDir(host, srcDir, destDir):
    cmd = "scp -r %s:%s %s" % (host, srcDir, destDir)
    rc,stdout,stderr = launch(cmd=cmd)
    assert(rc == 0), stderr


def convStringToJson(string):
    op = json.loads(string)
    assert(type(op) == type({})), "string could not be converted to json doct"
    return op



def doesFileExist(filepath, node):
    cmd = 'ssh %s test -e %s' % (node, filepath)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc == 0:
        return True
    return False


def doesRegularFileExist(filepath, node):
    cmd = 'ssh %s test -f %s' % (node, filepath)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc == 0:
        return True
    return False


def doesCommandPass(cmd):
    rc,stdout,stderr = launch(cmd=cmd)
    if rc == 0:
        return True
    return False

def getFileSource(filepath, node):
    cmd = 'ssh %s rpm -qf %s' % (node, filepath)
    stdout, stderr = general.eval_returns(cmd)
    return stdout.strip()

def getServiceStartTime(node, service_name):
    cmd = 'ssh %s systemctl show --property=ExecMainStartTimestamp %s' % (node, service_name)
    stdout, stderr = general.eval_returns(cmd)
    return stdout.strip()


class ListExceptions:
    excList = []
