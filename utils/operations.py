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
    