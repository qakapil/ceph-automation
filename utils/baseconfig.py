from ConfigParser import SafeConfigParser
import yaml
import unittest
import logging


def fetchIniData(filename):
    cfg = SafeConfigParser()
    return cfg.read(filename)

def fetchTestYamlData(yamlfile):
    document = open(yamlfile).read()
    return yaml.load(document)


def setLogger(logfile, cfg_data):
    LEVELS = {'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL}
    level_name = cfg_data.get('env','loglevel') 
    level = LEVELS.get(level_name, logging.NOTSET)
    logging.basicConfig(level=level,
            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
            datefmt='%m-%d %H:%M',
            filename=logfile,
            filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
