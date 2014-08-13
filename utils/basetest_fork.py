from ConfigParser import SafeConfigParser
import yaml
import unittest
import logging
import os


class Basetest(unittest.TestCase):
    config = None
    ctx = None
    
    def setUp(self):
        pass


    def tearDown(self):
        pass

    @staticmethod
    def fetchIniData(self):
        test_cfg = os.environ.get("TEST_CFG")
        if test_cfg == None:
            test_cfg = 'setup.cfg'
        self.config = SafeConfigParser()
        self.config.read(test_cfg)
        
     
       
        
    @staticmethod   
    def fetchTestYamlData(self, module):
        log = logging.getLogger("fetchTestYamlData")
        yaml_cfg = os.environ.get("TEST_YAML")
        if yaml_cfg == None:
            log.warning("Enviroment variable TEST_YAML is not set.")
            yaml_cfg = module.split('.')[len(module.split('.'))-1]
            yaml_cfg = 'yamldata/%s.yaml' % (yaml_cfg)
            log.debug("Defaulting yaml to:%s" % (yaml_cfg))
        document = open(yaml_cfg).read()
        self.ctx = yaml.load(document)
        
    
    @staticmethod   
    def setLogger(self):
        level_name = self.config.get('env','loglevel') 
        logFile = os.environ.get('TEST_LOG_CONF')
        if logFile != None:
            if os.path.isfile(str(options.log_config)):
                logging.config.fileConfig(options.log_config)
                return
            else:
                logging.basicConfig(level=LoggingLevel)
                log = logging.getLogger("main")
                log.error("Logfile configuration file '%s' was not found." % (options.log_config))
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
