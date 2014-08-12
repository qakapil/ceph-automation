from launch import launch
import logging
import os

log = logging.getLogger(__name__)



def restartCluster():
    pass


def createRBDImage(node, dictImg):
    name = dictImg.get('name', None)
    size = dictImg.get('size', None)
    pool = dictImg.get('pool', 'rbd')
    imglist = rbdGetPoolImages(node, pool)
    if name in imglist:
        rbdRemovePoolImage(node, dictImg)
    cmd = "ssh %s sudo rbd create %s --size %s --pool %s" % (node, name, size, pool)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)


def rbdGetPoolImages(node, poolname):
    cmd = "ssh %s sudo rbd -p %s ls" % (node, poolname)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    return stdout.strip().split('\n')

def rbdRemovePoolImage(node, dictImg):
    imgname = dictImg.get('name', None)
    poolname = dictImg.get('pool', 'rbd')
    cmd = "ssh %s sudo rbd -p %s rm %s" % (node, poolname, imgname)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    

def createValidateObject(node, dictObject):
    name = dictObject.get('objname', None)
    filename = dictObject.get('objname', None)+'.txt'
    pool = dictObject.get('pool', None)
    fo = open(filename, "w")
    fo.close()
    cmd = "ssh %s sudo rados put %s %s --pool=%s" % (node,
        name,
        filename,
        pool)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    os.remove(filename)
    cmd = "ssh %s sudo rados -p %s ls" % (node, pool)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    objlist = stdout.split('\n')
    assert (name in objlist),"object %s could not be created" % (name)
    log.info("created object %s " % (name))
    cmd = "ssh %s sudo ceph osd map %s %s" % (node, pool,name)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    log.info("the objectdetails are - %s " % (stdout))


def removeObject(node, dictObject):
    name = dictObject.get('objname', None)
    filename = dictObject.get('objname', None)+'.txt'
    pool = dictObject.get('pool', None)
    cmd = "ssh %s sudo rados -p %s ls" % (node, pool)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    objlist = stdout.split('\n')
    if (name not in objlist):
        log.warning("object %s does not exist" % (name))
        return
    cmd = "ssh %s sudo rados rm %s --pool=%s" % (node, name, pool)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    objlist = stdout.split('\n')
    assert (name not in objlist),"object %s could not be removed" % (name)
    log.info("removed the object - %s " % (name))
    

def createPool(node, dictPool):
    poolname = dictPool.get('poolname', None)
    pgnum = dictPool.get('pg-num', None)
    size = dictPool.get('size', None)
    cmd = "ssh %s sudo ceph osd lspools" % (node)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    poollist = stdout.split(',')
    if (poolname in poollist):
        log.warning("pool with name %s already exists" % (poolname))
        return
    cmd = "ssh %s sudo ceph osd pool create %s %s" % (node, poolname, pgnum)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    if (size is not None):
        cmd = "ssh %s sudo ceph osd pool set %s size %s" % (node, poolname, size)
        rc,stdout,stderr = launch(cmd=cmd)
        assert (rc == 0), "Error while executing the command %s.\
        Error message: %s" % (cmd, stderr)
    log.info("created the pool - %s " % (poolname))



def validatePool(node, dictPool):
    poolname = dictPool.get('poolname', None)
    pgnum = dictPool.get('pg-num', None)
    size = dictPool.get('size', None)
    cmd = "ssh %s sudo ceph osd lspools" % (node)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    poollist = stdout#.split(',')
    assert (poolname in poollist), "pool %s was not found in %s" % (poolname,poollist)
    cmd = "ssh %s sudo ceph osd pool get %s pg_num" % (node, poolname)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    act_pgnum = stdout.strip()
    assert (str(pgnum) in act_pgnum), "pgnum for pool %s were %s" % (poolname,str(act_pgnum))
    cmd = "ssh %s sudo ceph osd pool get %s size" % (node, poolname)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    act_size = stdout.strip()
    assert (str(size) in str(act_size)), "replica size for pool %s was %s" % (poolname,str(act_size))
    
    
def deletePool(node, dictPool):
    poolname = dictPool.get('poolname', None)
    cmd = "ssh %s sudo ceph osd pool delete %s %s --yes-i-really-really-mean-it" % (node, poolname, poolname)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    poollist = stdout#.split(',')
    assert (poolname not in poollist), "pool %s was not deleted in %s" % (poolname,poollist)

def restartCeph(node):
    cmd = "ssh %s sudo /etc/init.d/ceph restart" % (node)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)

def restartRadosGW(node):
    cmd = "ssh %s sudo /etc/init.d/ceph-radosgw restart" % (node)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    
    
