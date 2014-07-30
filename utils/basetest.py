from ConfigParser import SafeConfigParser
import yaml
import unittest
import logging

class Basetest(unittest.TestCase):
    config = None
    ctx = None
    
    def setUp(self):
        pass


    def tearDown(self):
        pass

    @staticmethod
    def fetchIniData(self):
        self.config = SafeConfigParser()
        self.config.read('setup.cfg')
        
     
       
        
    @staticmethod   
    def fetchTestYamlData(self, module):
        yamlfile = module.split('.')[len(module.split('.'))-1]
        yamlfile = 'yamldata/%s.yaml' % (yamlfile)
        document = open(yamlfile).read()
        self.ctx = yaml.load(document)
        
    
    @staticmethod   
    def setLogger(self):
        LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}
        level_name = self.config.get('env','loglevel') 
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
