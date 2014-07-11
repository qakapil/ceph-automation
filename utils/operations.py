from launch import launch
import logging

log = logging.getLogger(__name__)



def restartCluster():
    pass


def createRBDImages(**kwargs):
    name = kwargs.get('name', None)
    size = kwargs.get('size', None)
    pool = kwargs.get('pool', 'rbd')
    cmd = "rbd create %s --size %s --pool %s" % (name,size,pool)
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    