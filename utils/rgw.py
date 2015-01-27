import os, sys
from launch import launch
import logging
from ConfigParser import SafeConfigParser

log = logging.getLogger(__name__)

def create_rgw(rgw-host, rgw-name):
    deleteOldRgwData(rgw-host)
    cmd = "ssh %s ceph-deploy --overwrite-conf rgw create %s:%s"\
    % (os.environ["CLIENTNODE"], rgw-host, rgw-name)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.error("error while creating rgw %s on %s " % (rgw-name, rgw-host))
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    log.info("created rgw %s on %s " % (rgw-name, rgw-host))

    cmd = "curl %s.suse.de"% (rgw-host)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    anonymus_op = '<?xml version="1.0" encoding="UTF-8"?><ListAllMyBucketsResult\
xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Owner><ID>anonymous</ID>\
<DisplayName></DisplayName></Owner><Buckets></Buckets></ListAllMyBucketsResult>'
    assert (stdout.strip()==anonymus_op), "gateway did not give proper response"


def deleteOldRgwData(rgw-host):
    cmd = "ssh %s sudo rm -rf /srv/www/radosgw" % (rgw-host)
    rc,stdout,stderr = launch(cmd=cmd)

    cmd = "ssh %s sudo rm -rf /var/run/ceph-radosgw" % (rgw-host)
    rc,stdout,stderr = launch(cmd=cmd)

def verifyRGWList(rgw-name):
    cmd = "ssh %s ceph-deploy rgw list" % (os.environ["CLIENTNODE"])
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        log.error("error while getting rgw list")
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr)
    log.info("rgw list output %s" % stdout.strip())
    rgw_list = stdout.split('/n')[3 : ]
    assert (rgw-name in rgw_list), "gateway name was not found in rgw list"


def prepareS3Conf(rgw-data):
    rgw-data['random'] = 'random' #fix to manage the {random} tag in the conf template
    f = open('yamldata/s3-tests.conf.template','r')
    data = f.read()
    f.close()
    data = data.format(**rgw-data))
    cmd = "rm -rf s3tests ; mkdir s3tests"
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while executing the command '%s'. Error message: '%s'" % (cmd, stderr
    f = open('s3tests/s3-tests.conf','w')
    f.write(data)
    f.close()


def createS3TestsUsers(rgw-node, rgw-name):
    config = SafeConfigParser()
    config.read('s3tests/s3-tests.conf') 
    s3main_list = config.items('s3 main')[3:]
    s3main_data = {}
    s3main_data['client_key'] = "client.radosgw.%s" % (rgw-name)
    for i in range (len(s3main_list)):
        s3main_data[s3main_list[i][0]] = s3main_list[i][1]

    s3main_usercreate_cmd = "sudo radosgw-admin -n {client_key} user create {user_id} --display-name={display_name} \
--email={email} --access_key={access_key} --secret={secret_key} --key-type s3".format(**s3main_data)
   
    cmd = "ssh %s %s" % (rgw-node, s3main_usercreate_cmd)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while creating s3 main user'. Error message: '%s'" % (cmd, stderr)


    s3alt_list = config.items('s3 alt')[3:]
    s3alt_data = {} 
    s3alt_data['client_key'] = "client.radosgw.%s" % (rgw-name)
    for i in range (len(s3alt_list)):
        s3alt_data[s3alt_list[i][0]] = s3alt_list[i][1]

    s3alt_usercreate_cmd = "sudo radosgw-admin -n {client_key} user create {user_id} --display-name={display_name} \
--email={email} --access_key={access_key} --secret={secret_key} --key-type s3".format(**s3alt_data)
   
    cmd = "ssh %s %s" % (rgw-node, s3alt_usercreate_cmd)
    rc,stdout,stderr = launch(cmd=cmd)
    if rc != 0:
        raise Exception, "Error while creating s3 alt user'. Error message: '%s'" % (cmd, stderr)

