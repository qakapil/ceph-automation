from launch import launch
import logging, sys, os

log = logging.getLogger(__name__)


def cleanupCalamari():
    cmd = 'ssh %s sudo zypper rm calamari-server-test calamari-clients calamari-server' % (os.environ["CALAMARI_NODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.warning("Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr))
    
    cmd = 'ssh %s sudo rcpostgresql stop' % (os.environ["CALAMARI_NODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.warning("Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr))

    cmd = 'ssh %s sudo rm -rf /var/lib/pgsql/data' % (os.environ["CALAMARI_NODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.warning("Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr))

def initializeCalamari():
    cmd = '''ssh %s "sudo expect \
    -c 'spawn calamari-ctl initialize' \
    -c 'expect Username' \
    -c 'send root\n' \
    -c 'expect Email' \
    -c 'send root@example.com\n' \
    -c 'expect Password' \
    -c 'send linux\n' \
    -c 'expect Password' \
    -c 'send linux\n' \
    -c 'expect eof'"''' % (os.environ["CALAMARI_NODE"])
    
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    
    log.info(stdout)
    
    cmd = 'ssh %s sudo rcapache2 restart' % (os.environ["CALAMARI_NODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)

    cmd = 'ssh %s sudo wget -O /dev/null http://localhost/' % (os.environ["CALAMARI_NODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)

def runUnitTests():
    cmd = "sudo \
      CALAMARI_CONFIG=/etc/calamari/calamari.conf \
      DJANGO_SETTINGS_MODULE=calamari_web.settings \
      nosetests -v /usr/lib/python2.7/site-packages/calamari-server-test/cthulhu/tests"
    
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    
    log.info(stdout)
    

def runRestAPITests():
    cmd = "sudo \
      CALAMARI_CONFIG=/etc/calamari/calamari.conf \
      DJANGO_SETTINGS_MODULE=calamari_web.settings \
      nosetests -v /usr/lib/python2.7/site-packages/calamari-server-test/rest-api/tests"
    
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    
    log.info(stdout)
    

