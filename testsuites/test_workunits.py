from utils import monitoring
from utils import operations
from utils import baseconfig
from utils import general
from utils import cephdeploy
from utils import zypperutils
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

    before_cleanup = os.environ.get("BEFORE_CLEANUP")
    if before_cleanup != None:
        log.info('starting teardown for before_cleanup')
        general.perNodeCleanUp(yaml_data['allnodes'], 'ceph')

    if not monitoring.isClusterReady(60):
        operations.createCephCluster(yaml_data, cfg_data)
    status = monitoring.isClusterReady(300)
    assert status is True, "Ceph cluster was not ready. Failing the test suite"
    for pkg in ['ceph-test','ceph-devel','ceph-devel']:
        zypperutils.installPkgFromRepo(pkg, os.environ["CLIENTNODE"], 'ceph')


def test_workunit():
    global vErrors
    try:
        cmd = 'ssh %s rm /tmp/%s.tar.gz || true' % (os.environ["CLIENTNODE"], yaml_data['ceph_branch'])
        general.eval_returns(cmd)
        url = 'https://github.com/SUSE/ceph/archive/%s.tar.gz' % (yaml_data['ceph_branch'])
        cmd = 'ssh %s wget -O /tmp/%s.tar.gz %s' % (os.environ["CLIENTNODE"], yaml_data['ceph_branch'], url)
        general.eval_returns(cmd)
        cmd = 'ssh %s sudo rm -rf %s' % (os.environ["CLIENTNODE"], yaml_data['test_dir'])
        general.eval_returns(cmd)
        for workunit in yaml_data['workunits']:
            for suite in workunit:
                yaml_data['test_dir'] = '%s/%s' % (yaml_data['test_dir'], suite)
                cmd = 'ssh %s mkdir -p %s' % (os.environ["CLIENTNODE"], yaml_data['test_dir'])
                general.eval_returns(cmd)
                cmd = 'ssh %s tar --strip-components=4 -C %s -xvf /tmp/%s.tar.gz ceph-%s/qa/workunits/%s' % \
                (os.environ["CLIENTNODE"], yaml_data['test_dir'], yaml_data['ceph_branch'], yaml_data['ceph_branch'], suite)
                general.eval_returns(cmd)
            cmd = 'ssh %s ls %s' % (os.environ["CLIENTNODE"], yaml_data['test_dir'])
            stdout, stderr = general.eval_returns(cmd)
            excluded_scripts = workunit[suite]['excludes']
            test_scripts = stdout.split('\n')
            for files in excluded_scripts:
                if files in test_scripts:
                    test_scripts.pop(files)
            test_scripts = test_scripts[:len(test_scripts)-1]
            log.info('Following tests will be executed -> \n%s' % str(test_scripts))
            for script in test_scripts:
                log.info('\n*********************************************************\n')
                yield run_script, suite, script
    except Exception:
      exc_type, exc_value, exc_traceback = sys.exc_info()
      log.error(str(exc_type)+" : "+str(exc_value)+" : "+str(exc_traceback))
      sError = str(sys.exc_info()[0])+" : "+str(sys.exc_info()[1])
      log.error(inspect.stack()[0][3] + "Failed with error - "+sError)
      vErrors.append(sError)
      raise Exception(str(sys.exc_info()[1]))


def run_script(workunit, script_name):
    log.info('Executing %s tests from %s dir' % (script_name, workunit))
    cmd = 'ssh %s %s/%s' % (os.environ["CLIENTNODE"], yaml_data['test_dir'], script_name)
    stdout, stderr = general.eval_returns(cmd)
    log.info('test output stdout -> %s' % (stdout))
    log.info('test output stderr -> %s' % (stderr))


def teardown_module():
    log.info('++++++completed test suite ++++++')
    if vErrors:
        log.info('test suite failed with these errors - '+str(vErrors))
    else:
        log.info('starting teardown in teardown_module')
        #general.perNodeCleanUp(yaml_data['allnodes'], 'ceph')
        cephdeploy.cleanupNodes(yaml_data['allnodes'], 'ceph')
