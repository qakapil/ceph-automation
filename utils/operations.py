from launch import launch
import logging

log = logging.getLogger(__name__)



def restartCluster():
    pass


def createRBDImages(dictImg):
    name = dictImg.get('name', None)
    size = dictImg.get('size', None)
    pool = dictImg.get('pool', 'rbd')
    cmd = "rbd create %s --size %s --pool %s" % (name,size,pool)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)

def createValidateObject(dictObject):
    name = dictObject.get('objname', None)
    filename = dictObject.get('objname', None)+'.txt'
    pool = dictObject.get('pool', None)
    fo = open(filename, "w")
    fo.close()
    cmd = "rados put %s %s --pool=%s" % (name,filename,pool)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    cmd = "rados -p %s ls" % (pool)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    objlist = stdout.split('\n')
    assert (name in objlist),"object %s could not be created" % (name)
    log.info("created object %s " % (name))
    cmd = "ceph osd map %s %s" % (pool,name)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info("the objectdetails are - %s " % (stdout))


def removeObject(dictObject):
    name = dictObject.get('objname', None)
    filename = dictObject.get('objname', None)+'.txt'
    pool = dictObject.get('pool', None)
    cmd = "rados -p %s ls" % (pool)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    objlist = stdout.split('\n')
    if (name not in objlist):
        log.warning("object %s does not exist" % (name))
        return
    cmd = "rados rm %s --pool=%s" % (name,pool)
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
    cmd = "ceph osd lspools"
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    poollist = stdout.split(',')
    if (poolname in poollist):
        log.warning("pool with name %s already exists" % (poolname))
        return
    cmd = "ceph osd pool create %s %s" % (poolname, pgnum)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    if (size is not None):
        cmd = "ceph osd pool set %s size %s" % (poolname, size)
        rc,stdout,stderr = launch(cmd=cmd)
        assert (rc == 0), "Error while executing the command %s.\
        Error message: %s" % (cmd, stderr)
    log.info("created the pool - %s " % (poolname))



def validatePool(dictPool):
    poolname = dictPool.get('poolname', None)
    pgnum = dictPool.get('pg-num', None)
    size = dictPool.get('size', None)
    cmd = "ceph osd lspools"
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    poollist = stdout#.split(',')
    assert (poolname in poollist), "pool %s was not found in %s" % (poolname,poollist)
    cmd = "ceph osd pool get %s pg_num" % (poolname)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    act_pgnum = stdout.strip()
    assert (int(act_pgnum)==int(pgnum)), "pgnum for pool %s were %s" % (poolname,str(act_pgnum))
    cmd = "ceph osd pool get %s size" % (size)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    act_size = stdout.strip()
    assert (int(act_size)==int(size)), "replica size for pool %s was %s" % (poolname,str(act_size))
    
    
    