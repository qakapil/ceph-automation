from launch import launch
import logging, sys, os
import zypperutils

log = logging.getLogger(__name__)


def cleanupCalamari():    
    try:
        zypperutils.removePkg('calamari-server-test calamari-clients calamari-server', os.environ["CALAMARI_NODE"])
    except Exception as e:
        log.warning("Error while removing ceph-deploy "+str(sys.exc_info()[0]))
    
    cmd = 'ssh %s sudo rcpostgresql stop' % (os.environ["CALAMARI_NODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.warning("Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr))

    cmd = 'ssh %s sudo rm -rf /var/lib/pgsql/data' % (os.environ["CALAMARI_NODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.warning("Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr))
    
    cmd = 'ssh %s sudo rm -rf /usr/lib/python2.7/site-packages/calamari-server-test/' % (os.environ["CALAMARI_NODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.warning("Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr))
        

def initializeCalamari():
    cmd = '''ssh %s "sudo expect \
    -c 'spawn calamari-ctl initialize' \
    -c 'expect Username' \
    -c 'send root' \
    -c 'expect Email' \
    -c 'send root@example.com' \
    -c 'expect Password' \
    -c 'send linux' \
    -c 'expect Password' \
    -c 'send linux' \
    -c 'expect eof'"''' % (os.environ["CALAMARI_NODE"])
    
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    
    log.info(stdout)
    
    '''cmd = 'ssh %s sudo rcapache2 restart' % (os.environ["CALAMARI_NODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)''' #this bug got fixed #893351

    cmd = 'ssh %s sudo wget -O /dev/null http://localhost/' % (os.environ["CALAMARI_NODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)

def runUnitTests():
    cmd = "ssh %s sudo \
      CALAMARI_CONFIG=/etc/calamari/calamari.conf \
      DJANGO_SETTINGS_MODULE=calamari_web.settings \
      nosetests -v /usr/lib/python2.7/site-packages/calamari-server-test/cthulhu/tests" % (os.environ["CALAMARI_NODE"])
    
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    
    log.info(stderr)  #this needs to be fixed. stdout doesn't conatin the output
    

def runRestAPITests():
    cmd = "ssh %s sudo \
      CALAMARI_CONFIG=/etc/calamari/calamari.conf \
      DJANGO_SETTINGS_MODULE=calamari_web.settings \
      nosetests -v /usr/lib/python2.7/site-packages/calamari-server-test/rest-api/tests" % (os.environ["CALAMARI_NODE"])
    
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    
    log.info(stderr) #this needs to be fixed. stdout doesn't conatin the output


def copyClusterConf(yamlfile):
    cmd = 'scp utils/test.conf %s:/tmp' % (os.environ["CALAMARI_NODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    
    cmd = 'ssh %s sudo cp /tmp/test.conf /usr/lib/python2.7/site-packages/calamari-server-test/tests' % (os.environ["CALAMARI_NODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    
    cmd = 'scp %s %s:/tmp/calamari_cluster.yaml' % (yamlfile, os.environ["CALAMARI_NODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    
    
    