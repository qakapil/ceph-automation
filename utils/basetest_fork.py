from ConfigParser import SafeConfigParser
import yaml
import unittest
import logging
import os
import os.path


def decorate_config_ini(wollmilchsau):
    log = logging.getLogger("decorate_config_ini")
    test_cfg = os.environ.get("TEST_CFG")
    log.debug(test_cfg)
    if test_cfg == None:
        log.warning("Enviroment variable TEST_CFG is not set.")
        test_cfg = 'setup.cfg'
        log.debug("defaulting to '%s'" % (test_cfg))
    wollmilchsau.config = SafeConfigParser()
    if os.path.isfile(str(test_cfg)):
        wollmilchsau.config.read(test_cfg)
    else:
        log.error("Configuration file '%s' was not found." % (test_cfg))
        assert(False)




def decorate_config_yaml(wollmilchsau, module):
    log = logging.getLogger("decorate_config_yaml")
    yaml_cfg = os.environ.get("TEST_YAML")
    if yaml_cfg == None:
        log.warning("Enviroment variable TEST_YAML is not set.")
        yaml_cfg = module.split('.')[len(module.split('.'))-1]
        yaml_cfg = 'yamldata/%s.yaml' % (yaml_cfg)
        log.debug("Defaulting yaml to:%s" % (yaml_cfg))
    document = open(yaml_cfg).read()
    wollmilchsau.ctx = yaml.load(document)



def decorate_logger():
    level_name = os.environ.get('TEST_LOG_LEVEL')
    if level_name == None:
        level_name = 'debug'
    logFile = os.environ.get('TEST_LOG_CONF')
    if logFile != None:
        if os.path.isfile(str(logFile)):
            logging.config.fileConfig(logFile)
            return
        else:
            logging.basicConfig(level=LoggingLevel)
            log = logging.getLogger("main")
            log.error("Logfile configuration file '%s' was not found." % (logFile))
            assert(False)
    LEVELS = {'debug': logging.DEBUG,
      'info': logging.INFO,
      'warning': logging.WARNING,
      'error': logging.ERROR,
      'critical': logging.CRITICAL} 
    level = LEVELS.get(level_name, logging.NOTSET)
    logging.basicConfig(level=level,
                format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                datefmt='%m-%d %H:%M',
                filename='cephauto.log',
                filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
