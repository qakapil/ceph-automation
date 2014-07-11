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
    