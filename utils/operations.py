from launch import launch
import logging
import os, time
import monitoring
from utils import zypperutils
from utils import cephdeploy

log = logging.getLogger(__name__)



def restartCluster():
    pass


def createValidateObject(dictObject):
    name = dictObject.get('objname', None)
    filename = dictObject.get('objname', None)+'.txt'
    pool = dictObject.get('pool', None)
    #fo = open(filename, "w")
    #fo.close()
    cmd = "ssh %s touch %s " %(os.environ["CLIENTNODE"], filename)
    
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    
    cmd = "ssh %s rados put %s %s --pool=%s" % (os.environ["CLIENTNODE"],name,filename,pool)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    #os.remove(filename)
    cmd = "ssh %s rm %s" %(os.environ["CLIENTNODE"], filename)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr) 
    cmd = "ssh %s rados -p %s ls" % (os.environ["CLIENTNODE"],pool)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    objlist = stdout.split('\n')
    assert (name in objlist),"object %s could not be created" % (name)
    log.info("created object %s " % (name))
    cmd = "ssh %s ceph osd map %s %s" % (os.environ["CLIENTNODE"],pool,name)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info("the objectdetails are - %s " % (stdout))


def removeObject(dictObject):
    name = dictObject.get('objname', None)
    filename = dictObject.get('objname', None)+'.txt'
    pool = dictObject.get('pool', None)
    cmd = "ssh %s rados -p %s ls" % (os.environ["CLIENTNODE"],pool)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    objlist = stdout.split('\n')
    if (name not in objlist):
        log.warning("object %s does not exist" % (name))
        return
    cmd = "ssh %s rados rm %s --pool=%s" % (os.environ["CLIENTNODE"],name,pool)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    objlist = stdout.split('\n')
    assert (name not in objlist),"object %s could not be removed" % (name)
    log.info("removed the object - %s " % (name))
    

def createPool(dictPool):
    poolname = dictPool.get('poolname', None)
    pgnum = dictPool.get('pg-num', None)
    size = dictPool.get('size', None)
    cmd = "ssh %s ceph osd lspools" % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    poollist = stdout.split(',')
    if (poolname in poollist):
        log.warning("pool with name %s already exists" % (poolname))
        return
    cmd = "ssh %s ceph osd pool create %s %s" % (os.environ["CLIENTNODE"], poolname, pgnum)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    if (size is not None):
        cmd = "ssh %s ceph osd pool set %s size %s" % (os.environ["CLIENTNODE"],poolname, size)
        rc,stdout,stderr = launch(cmd=cmd)
        assert (rc == 0), "Error while executing the command %s.\
        Error message: %s" % (cmd, stderr)
    log.info("created the pool - %s " % (poolname))


def changePoolReplica(dictPool):
    poolname = dictPool.get('poolname', None)
    size = dictPool.get('size', None)
    cmd = "ssh %s ceph osd pool set %s size %s" % (os.environ["CLIENTNODE"], poolname, size)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info("changed the pool - %s to replica size %s" % (poolname, size))


def validatePool(dictPool):
    poolname = dictPool.get('poolname', None)
    pgnum = dictPool.get('pg-num', None)
    size = dictPool.get('size', None)
    cmd = "ssh %s ceph osd lspools" % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    poollist = stdout#.split(',')
    assert (poolname in poollist), "pool %s was not found in %s" % (poolname,poollist)
    cmd = "ssh %s ceph osd pool get %s pg_num" % (os.environ["CLIENTNODE"],poolname)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    act_pgnum = stdout.strip()
    assert (str(pgnum) in act_pgnum), "pgnum for pool %s were %s" % (poolname,str(act_pgnum))
    cmd = "ssh %s ceph osd pool get %s size" % (os.environ["CLIENTNODE"],poolname)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    act_size = stdout.strip()
    assert (str(size) in str(act_size)), "replica size for pool %s was %s" % (poolname,str(act_size))
    
    
def deletePool(dictPool):
    poolname = dictPool.get('poolname', None)
    cmd = "ssh %s ceph osd pool delete %s %s --yes-i-really-really-mean-it" % (os.environ["CLIENTNODE"],poolname,poolname)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    poollist = stdout#.split(',')
    assert (poolname not in poollist), "pool %s was not deleted in %s" % (poolname,poollist)


def restartCeph(node):
    cmd = "ssh %s sudo ls /etc/init.d/ceph" % (node)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.warn('this is not a systemV ceph. using systemd restart')
        cmd = "ssh %s sudo rcceph restart" % (node)
        rc,stdout,stderr = launch(cmd=cmd)
        assert (rc == 0), "Error while executing the command %s.\
        Error message: %s" % (cmd, stderr)
        return
    cmd = "ssh %s sudo /etc/init.d/ceph restart" % (node)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)


def restartRadosGW(node):
    cmd = "ssh %s sudo ls /etc/init.d/ceph" % (node)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.info('restarting radosgw with systemd')
        cmd = "ssh %s sudo systemctl list-units --type service  | grep ceph-radosgw | grep -v failed" % (node)
        rc,stdout,stderr = launch(cmd=cmd)
        assert (rc == 0), "Error while executing the command %s.\
        Error message: %s" % (cmd, stderr)

        all_services = stdout.split("\n")
        list_services = []
        for service in all_services:
            list_services.append(service.split(" ")[0])

        assert (len(list_services) > 1), "no systemd service found for radosgw"
        for i in range(len(list_services)-1):
            cmd = "ssh %s sudo systemctl restart %s" % (node, list_services[i])
            rc,stdout,stderr = launch(cmd=cmd)
            assert (rc == 0), "Error while executing the command %s.\
            Error message: %s" % (cmd, stderr)
    else:
        log.info('restarting radosgw with sysV')
        cmd = "ssh %s sudo /etc/init.d/ceph-radosgw restart" % (node)
        rc,stdout,stderr = launch(cmd=cmd)
        assert (rc == 0), "Error while executing the command %s.\
        Error message: %s" % (cmd, stderr)


def manageAllCephServices(node, action):
    cmd = "ssh %s sudo rcceph %s" % (node, action)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
            Error message: %s" % (cmd, stderr)


def actionOnCephService(node, action):
    #action - start|stop|restart
    cmd = "ssh %s sudo ls /etc/init.d/ceph-dummy" % (node) #temporary dummy workaround
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.info('performing action on ceph service with systemd')
        if action != 'start':
            cmd = "ssh %s sudo systemctl list-units --type service | grep ceph | grep -v failed" % (node)
        else:
            cmd = "ssh %s sudo systemctl list-units --type service --all | grep ceph | grep inactive | grep -v ceph-disk | grep -v not-found" % (node)
        rc,stdout,stderr = launch(cmd=cmd)
        assert (rc == 0), "Error while executing the command %s.\
        Error message: %s" % (cmd, stderr)

        all_services = stdout.split("\n")
        list_services = []
        for service in all_services:
            list_services.append(service.split(" ")[0])

        assert (len(list_services) > 1), "no systemd service found for ceph"
        for i in range(len(list_services)-1):
            cmd = "ssh %s sudo systemctl %s %s" % (node, action, list_services[i])
            rc,stdout,stderr = launch(cmd=cmd)
            assert (rc == 0), "Error while executing the command %s.\
            Error message: %s" % (cmd, stderr)
    else:
        log.info('performing action on ceph services with sysV')
        cmd = "ssh %s sudo /etc/init.d/ceph %s" % (node, action)
        rc,stdout,stderr = launch(cmd=cmd)
        assert (rc == 0), "Error while executing the command %s.\
        Error message: %s" % (cmd, stderr)


def validateLibRbdTests():
        cmd = "cat librbd_tests.py | ssh %s python" % (os.environ["CLIENTNODE"])
        rc,stdout,stderr = launch(cmd=cmd)
        for output in stdout.split('\n'):
            log.info(output)
        assert (rc == 0), "Error while executing the command %s.\
        Error message: %s" % (cmd, stderr)
   

def setPGNUM(pg_num):
    total_pgs = 0
    cmd = "ssh %s rados lspools" % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.Error message: %s" % (cmd, stderr)
    pools = stdout.strip()
    pools = stdout.split("\n")
    for pool in pools:
        if pool != '':
            cmd = "ssh %s ceph osd pool set %s pg_num %s" % (os.environ["CLIENTNODE"],pool.strip(),pg_num)
            rc,stdout,stderr = launch(cmd=cmd)
            assert (rc == 0), "Error while executing the command %s.Error message: %s" % (cmd, stderr)
            total_pgs = total_pgs + int(pg_num)
    time.sleep(15)
    for pool in pools:
        if pool != '':
            cmd = "ssh %s ceph osd pool set %s pgp_num %s" % (os.environ["CLIENTNODE"],pool.strip(),pg_num)
            rc, stdout,stderr = launch(cmd=cmd)
            assert (rc == 0), "Error while executing the command %s.Error message: %s" % (cmd, stderr)
    actual_pgs = monitoring.getTotalPGs()
    #from utils import monitoring
    assert (int(actual_pgs) == int(total_pgs)), "All PGs were not created"


def createCephCluster(yaml_data, cfg_data):
    url = cfg_data.get('env', 'repo_baseurl')
    for node in yaml_data['allnodes']:
        zypperutils.addRepo('ceph', url, node)
    zypperutils.installPkg('ceph-deploy', os.environ["CLIENTNODE"])
    cephdeploy.declareInitialMons(yaml_data['initmons'])
    cephdeploy.installNodes(yaml_data['allnodes'])
    cephdeploy.createInitialMons(yaml_data['initmons'])
    if yaml_data['osd_zap'] is not None:
        cephdeploy.osdZap(yaml_data['osd_zap'])
    cephdeploy.osdPrepare(yaml_data['osd_prepare'])
    cephdeploy.osdActivate(yaml_data['osd_activate'])
    cephdeploy.addAdminNodes(yaml_data['clientnode'])


