import download
import logging
import optparse
import os
import sys
from __version__ import version

def main():
    log = logging.getLogger("main")
    """Runs program and handles command line options"""
    p = optparse.OptionParser(version = "%prog " + version)
    p.add_option('-v', '--verbose', action ='count',help='Change global log level, increasing log output.', metavar='LOGFILE')
    p.add_option('-q', '--quiet', action ='count',help='Change global log level, decreasing log output.', metavar='LOGFILE')
    p.add_option('--branch', action ='store',help='set branch to commit rpms to.', metavar='OBSREPOARCH_BRANCH')
    p.add_option('--repo-uri', action ='store',help='base uri to downlaod', metavar='OBSREPOARCH_URI')
    p.add_option('--git-master-repo', action ='store',help='local shared git pack object store path', metavar='OBSREPOARCH_MASTERREPO')
    p.add_option('--git-origin', action ='store',help='upstream git repo.', metavar='OBSREPOARCH_ORIGIN')
    p.add_option('--dir-work', action ='store',help='Working directory fro checkout of repo.', metavar='OBSREPOARCH_WORKINGDIR')
    p.add_option('--log-config', action ='store',help='Logfile configuration file, (overrides command line).', metavar='LOGFILE')
    options, arguments = p.parse_args()
    logFile = None
    workingdir = 'workingdir'
    origin = ''
    shared_clone = ''
    branch = "ibs_product_1.0"
    uri = "http://download.suse.de/ibs/Devel:/Storage:/1.0:/Staging/openSUSE_Factory/"
    if 'OBSREPOARCH_LOG_CONF' in os.environ:
        logFile = os.environ['OBSREPOARCH_LOG_CONF']
    if 'OBSREPOARCH_ORIGIN' in os.environ:
        origin = os.environ['OBSREPOARCH_ORIGIN']
    if 'OBSREPOARCH_WORKINGDIR' in os.environ:
        workingdir = os.environ['OBSREPOARCH_WORKINGDIR']
    if 'OBSREPOARCH_BRANCH' in os.environ:
        branch = os.environ['OBSREPOARCH_BRANCH']
    if 'OBSREPOARCH_URI' in os.environ:
        uri = os.environ['OBSREPOARCH_URI']
    if 'OBSREPOARCH_MASTERREPO' in os.environ:
        shared_clone = os.environ['OBSREPOARCH_MASTERREPO']
    LoggingLevel = logging.WARNING
    LoggingLevelCounter = 2
    if options.verbose:
        LoggingLevelCounter = LoggingLevelCounter - options.verbose
        if options.verbose == 1:
            LoggingLevel = logging.INFO
        if options.verbose == 2:
            LoggingLevel = logging.DEBUG
    if options.quiet:
        LoggingLevelCounter = LoggingLevelCounter + options.quiet
    if LoggingLevelCounter <= 0:
        LoggingLevel = logging.DEBUG
    if LoggingLevelCounter == 1:
        LoggingLevel = logging.INFO
    if LoggingLevelCounter == 2:
        LoggingLevel = logging.WARNING
    if LoggingLevelCounter == 3:
        LoggingLevel = logging.ERROR
    if LoggingLevelCounter == 4:
        LoggingLevel = logging.FATAL
    if LoggingLevelCounter >= 5:
        LoggingLevel = logging.CRITICAL

    if options.log_config:
        logFile = options.log_config
    if logFile != None:
        if os.path.isfile(str(options.log_config)):
            logging.config.fileConfig(options.log_config)
        else:
            logging.basicConfig(level=LoggingLevel)
            log = logging.getLogger("main")
            log.error("Logfile configuration file '%s' was not found." % (options.log_config))
            sys.exit(1)
    else:
        logging.basicConfig(level=LoggingLevel)
    log = logging.getLogger("main")
    if options.branch:
        branch = options.branch
    if options.repo_uri:
        uri = options.repo_uri
    if options.dir_work:
        workingdir = options.dir_work
    if options.git_master_repo:
        shared_clone = options.git_master_repo
    if not options.git_origin:
        log.error("No git origin given, use --git-origin!")
        sys.exit(1)
    origin = options.git_origin

    downloader = download.downloader(
        workingdir=workingdir,
        origin=origin,
        shared_clone=shared_clone
        )
    downloader.work_dir_setup()
    downloader.update(
        branch=branch,
        uri=uri
        )
    return 0
