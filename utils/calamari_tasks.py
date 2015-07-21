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
    
    cmd = 'ssh %s sudo rm expect /tmp/calamari_cluster.yaml /tmp/test.conf' % (os.environ["CALAMARI_NODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.warning("Error while executing the command '%s'. Error message: '%s'" % (cmd, str(stderr).strip()))

    cmd = "ssh %s sudo rm -rf /etc/salt/*" % (os.environ["CALAMARI_NODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.warning("Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr))
        
        
        

def initializeCalamari():
    cmd = "ssh %s sudo systemctl restart apache2.service" % (os.environ["CALAMARI_NODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)

    cmd = "scp utils/expect %s:~" % (os.environ["CALAMARI_NODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    
    cmd = "ssh %s sudo chmod 755 expect" % (os.environ["CALAMARI_NODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    
    cmd = "ssh %s sudo ./expect" % (os.environ["CALAMARI_NODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    
    log.info(stdout)
    
    #cmd = 'ssh %s sudo rcapache2 restart' % (os.environ["CALAMARI_NODE"])
    #rc,stdout,stderr = launch(cmd=cmd)
    #assert (rc == 0), "Error while executing the command %s.\
    #Error message: %s" % (cmd, stderr)#this bug got fixed #893351
       
    cmd = 'ssh %s sudo wget -O /dev/null http://localhost/' % (os.environ["CALAMARI_NODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    
    

def runUnitTests():

    cmd = "ssh %s sudo /usr/lib/python2.7/site-packages/calamari-server-test/run-unit-tests" % (os.environ["CALAMARI_NODE"])
    
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


def cleanupStaleNodes(listNodes):
    for node in listNodes:
        cmd = "ssh %s sudo systemctl stop salt-minion" % (node)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            log.warning("Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr))
        cmd = "ssh %s sudo systemctl disable salt-minion" % (node)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            log.warning("Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr))
        cmd = "ssh %s sudo systemctl stop diamond" % (node)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            log.warning("Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr))
        cmd = "ssh %s sudo systemctl disable diamond" % (node)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            log.warning("Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr))
        cmd = "ssh %s sudo rm -rf /etc/salt/*" % (node)
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            log.warning("Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr))
        
    
    


def runServerTests():

    cmd = "ssh %s sudo /usr/lib/python2.7/site-packages/calamari-server-test/run-server-tests"
    
    rc,stdout,stderr = launch(cmd=cmd)
    assert (rc == 0), "Error while executing the command %s.\
    Error message: %s" % (cmd, stderr)
    
    log.info(stderr) #this needs to be fixed. stdout doesn't conatin the output
