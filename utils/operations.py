from launch import launch
import logging

log = logging.getLogger(__name__)



def restartCluster():
    cmd = 'ceph restart'
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. \
                          Error message: '%s'" % (cmd, stderr)
    log.info('restarted the ceph cluster successfully')
    