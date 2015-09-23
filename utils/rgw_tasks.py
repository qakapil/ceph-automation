import os, sys, time, socket
from launch import launch
import logging
from ConfigParser import SafeConfigParser

log = logging.getLogger(__name__)

def create_rgw(rgw_host, rgw_name, port='7480', apache=None):
    deleteOldRgwData(rgw_host)
    fqdn = socket.getfqdn(rgw_host)
    if apache:
        apache = '--cgi'
    else:
        apache = ''
    cmd = "ssh %s ceph-deploy --overwrite-conf rgw create %s:%s:%s:%s %s"\
    % (os.environ["CLIENTNODE"], rgw_host, rgw_name, fqdn, port, apache)
    cmd = cmd.strip()
    rc,stdout,stderr = launch(cmd=cmd)
    log.info(stdout +'----'+ stderr)
    if rc != 0:
        log.error("error while creating rgw %s on %s " % (rgw_name, rgw_host))
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    log.info("created rgw %s on %s " % (rgw_name, rgw_host))
    time.sleep(20)
    cmd = "curl %s:%s"% (rgw_host, port)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    anonymus_op = '<?xml version="1.0" encoding="UTF-8"?><ListAllMyBucketsResult \
xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Owner><ID>anonymous</ID>\
<DisplayName></DisplayName></Owner><Buckets></Buckets></ListAllMyBucketsResult>'
    assert (stdout.strip()==anonymus_op), "gateway gave bad response - "+ stdout +'----'+ stderr


def deleteOldRgwData(rgw_host):
    cmd = "ssh %s sudo rm -rf /srv/www/radosgw" % (rgw_host)
    rc,stdout,stderr = launch(cmd=cmd)

    cmd = "ssh %s sudo rm -rf /var/run/ceph-radosgw/*" % (rgw_host)
    rc,stdout,stderr = launch(cmd=cmd)

def verifyRGWList(rgw_host, rgw_name):
    cmd = "ssh %s ceph-deploy rgw list" % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.error("error while getting rgw list")
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    log.info("rgw list output %s" % stdout.strip())
    rgw_list = stdout.strip()
    assert (rgw_host+':'+rgw_name in rgw_list), "gateway name was not found in rgw list"


def prepareS3Conf(rgw_data):
    rgw_data['random'] = 'random' #fix to manage the {random} tag in the conf template
    fr = open('yamldata/s3-tests.conf.template','r')
    data = fr.read()
    fr.close()
    data = data.format(**rgw_data)
    cmd = "rm -rf s3tests ; mkdir s3tests"
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    fw = open('s3tests/s3-tests.conf','w')
    fw.write(data)
    fw.close()




def prepareSwiftConf(rgw_data):
    fr = open('yamldata/swift-tests.conf.template','r')
    data = fr.read()
    fr.close()
    data = data.format(**rgw_data)
    cmd = "rm -rf swifttests ; mkdir swifttests"
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    fw = open('swifttests/swift-tests.conf','w')
    fw.write(data)
    fw.close()


def createS3TestsUsers(rgw_node, rgw_name):
    config = SafeConfigParser()
    config.read('s3tests/s3-tests.conf') 
    s3main_list = config.items('s3 main')[3:]
    s3main_data = {}
    s3main_data['client_key'] = "client.radosgw.%s" % (rgw_name)
    for i in range (len(s3main_list)):
        s3main_data[s3main_list[i][0]] = s3main_list[i][1]

    s3main_usercreate_cmd = 'sudo radosgw-admin -n {client_key} user create --uid={user_id} --display-name=\"{display_name}\" \
--email={email} --access_key={access_key} --secret={secret_key} --key-type s3'.format(**s3main_data)
   
    cmd = "ssh %s %s" % (rgw_node, s3main_usercreate_cmd)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while creating s3 main user'. Error message: '%s'" % (stderr)


    s3alt_list = config.items('s3 alt')[3:]
    s3alt_data = {} 
    s3alt_data['client_key'] = "client.radosgw.%s" % (rgw_name)
    for i in range (len(s3alt_list)):
        s3alt_data[s3alt_list[i][0]] = s3alt_list[i][1]

    s3alt_usercreate_cmd = 'sudo radosgw-admin -n {client_key} user create --uid={user_id} --display-name=\"{display_name}\" \
--email={email} --access_key={access_key} --secret={secret_key} --key-type s3'.format(**s3alt_data)
   
    cmd = "ssh %s %s" % (rgw_node, s3alt_usercreate_cmd)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while creating s3 alt user'. Error message: '%s'" % (stderr)





def createSwiftTestsUsers(rgw_node, rgw_name):
    config = SafeConfigParser()
    config.read('swifttests/swift-tests.conf')
    swift_list = config.items('func_test')
    swift_data = {}
    swift_data['client_key'] = "client.radosgw.%s" % (rgw_name)
    for i in range (len(swift_list)):
        swift_data[swift_list[i][0]] = swift_list[i][1]

    swift_acc1_cmd = 'sudo radosgw-admin -n {client_key} user create --subuser={account}:{username} --display-name=\"{display_name}\" \
--email={email} --secret={password} --key-type swift --access=full'.format(**swift_data)

    cmd = "ssh %s %s" % (rgw_node, swift_acc1_cmd)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while creating swift account1 user'. Error message: '%s'" % (stderr)


    swift_acc2_cmd = 'sudo radosgw-admin -n {client_key} user create --subuser={account2}:{username2} --display-name=\"{display_name2}\" \
--email={email2} --secret={password2} --key-type swift --access=full'.format(**swift_data)

    cmd = "ssh %s %s" % (rgw_node, swift_acc2_cmd)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while creating swift account2 user'. Error message: '%s'" % (stderr)



def executeS3Tests():
    try:
        cmd = "rm /tmp/s3-tests.conf || true"
        rc,stdout,stderr = launch(cmd=cmd)
  
        cmd = "cp s3tests/s3-tests.conf /tmp/s3-tests.conf"
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)

        cmd = "git clone -b hammer https://github.com/SUSE/s3-tests.git s3tests/cloned"
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)

        cmd = "cd s3tests/cloned && ./bootstrap"
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)


        cmd = "S3TEST_CONF=/tmp/s3-tests.conf s3tests/cloned/virtualenv/bin/nosetests -w s3tests/cloned/ -a '!fails_on_rgw'"
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
        log.info(stderr.strip())
    finally:
        log.info("cleaning up s3tests dir ..") 
        cmd = "rm -rf s3tests && rm /tmp/s3-tests.conf"
        rc,stdout,stderr = launch(cmd=cmd)


def executeSwiftTests():
    try:
        cmd = "rm /tmp/swift-tests.conf || true"
        rc,stdout,stderr = launch(cmd=cmd)
  
        cmd = "cp swifttests/swift-tests.conf /tmp/swift-tests.conf"
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)

        cmd = "git clone https://github.com/SUSE/swift.git swifttests/cloned"
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)

        cmd = "cd swifttests/cloned && ./bootstrap"
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)


        cmd = "SWIFT_TEST_CONFIG_FILE=/tmp/swift-tests.conf swifttests/cloned/virtualenv/bin/nosetests\
        -w swifttests/cloned/test/functional -a '!fails_on_rgw'"
        rc,stdout,stderr = launch(cmd=cmd)
        if rc != 0:
            raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
        log.info(stderr.strip())
    finally:
        log.info("cleaning up swifttests dir ..")
        cmd = "rm -rf swifttests && rm /tmp/swift-tests.conf"
        rc,stdout,stderr = launch(cmd=cmd)

def delete_rgw(rgw_host, rgw_name):
    cmd = "ssh %s ceph-deploy --overwrite-conf rgw delete %s:%s" % (rgw_host, rgw_name, os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)

