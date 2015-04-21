from utils import monitoring
from utils import operations
from utils import baseconfig
from utils import general

import inspect
from ConfigParser import SafeConfigParser
import logging
import os
import sys

log = logging.getLogger(__name__)

cfg_data = None
yaml_data = {}
vErrors = []


def setup_module():
    global cfg_data
    global yaml_data
    filename = os.environ.get("CFG_FILE", "setup.cfg")
    cfg_data = SafeConfigParser()
    cfg_data.read(filename)

    yamlfile = os.environ.get("YAMLDATA_FILE")
    if yamlfile == None:
        yamlfile = __name__.split('.')[len(__name__.split('.'))-1]
        yamlfile = 'yamldata/%s.yaml' % (yamlfile)
    yaml_data = baseconfig.fetchTestYamlData(yamlfile)


    baseconfig.setLogger('cephauto.log', cfg_data)
    os.environ["CLIENTNODE"] = yaml_data['clientnode'][0]
    if not monitoring.isClusterReady(60):
        operations.createCephCluster(yaml_data, cfg_data)
    status = monitoring.isClusterReady(300)
    assert status is True, "Ceph cluster was not ready. Failing the test suite"


def test_workunit():
    global vErrors
    try:
        yaml_data['test_dir'] = '%s/%s' % (yaml_data['test_dir'], yaml_data['workunit_dir'])
        url = 'https://github.com/SUSE/ceph/archive/%s.tar.gz' % (yaml_data['ceph_branch'])
        cmd = 'ssh %s wget -O /tmp/%s.tar.gz %s' % (os.environ["CLIENTNODE"], yaml_data['ceph_branch'], url)
        general.eval_returns(cmd)
        cmd = 'ssh %s mkdir -p %s' % (os.environ["CLIENTNODE"], yaml_data['test_dir'])
        general.eval_returns(cmd)
        cmd = 'ssh %s tar --strip-components=4 -C %s -xvf /tmp/%s.tar.gz ceph-%s/qa/workunits/%s' % \
        (os.environ["CLIENTNODE"], yaml_data['test_dir'], yaml_data['ceph_branch'], yaml_data['ceph_branch'], yaml_data['workunit_dir'])
        general.eval_returns(cmd)
        cmd = 'ssh %s ls %s' % (os.environ["CLIENTNODE"], yaml_data['test_dir'])
        stdout, stderr = general.eval_returns(cmd)
        test_scripts = stdout.split('\n')
        test_scripts = test_scripts[:len(test_scripts)-1]
        for script in test_scripts:
            log.info('Executing %s tests from %s dir' % (script, yaml_data['workunit_dir']))
            run_script(yaml_data['workunit_dir'], script)

    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log.error(str(exc_type)+" : "+str(exc_value)+" : "+str(exc_traceback))
        sError = str(sys.exc_info()[0])+" : "+str(sys.exc_info()[1])
        log.error(inspect.stack()[0][3] + "Failed with error - "+sError)
        vErrors.append(sError)
        raise Exception(str(sys.exc_info()[1]))


def run_script(workunit_dir, script_name):
    log.info('Executing %s tests from %s dir' % (script_name, workunit_dir))
    cmd = 'ssh %s %s/%s' % (os.environ["CLIENTNODE"], yaml_data['test_dir'], script_name)
    general.eval_returns(cmd)


def teardown_module():
    log.info('++++++completed test suite ++++++')
    if vErrors:
        log.info('test suite failed with these errors - '+str(vErrors))
    else:
        log.info('starting teardown in teardown_module')
        general.perNodeCleanUp(yaml_data['allnodes'], 'ceph')
