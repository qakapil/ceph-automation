
obsrepoarch --help
Usage: obsrepoarch [options]

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Change global log level, increasing log output.
  -q, --quiet           Change global log level, decreasing log output.
  --branch=OBSREPOARCH_BRANCH
                        set branch to commit rpms to.
  --repo-uri=OBSREPOARCH_URI
                        base uri to downlaod
  --git-origin=OBSREPOARCH_ORIGIN
                        upstream git repo.
  --git-master-repo=OBSREPOARCH_MASTERREPO
                        local shared git pack object store path.
  --dir-work=OBSREPOARCH_WORKINGDIR
                        Working directory fro checkout of repo.
  --log-config=LOGFILE  Logfile configuration file, (overrides command line).


Enviroment variables:

OBSREPOARCH_URI
OBSREPOARCH_BRANCH
OBSREPOARCH_WORKINGDIR
OBSREPOARCH_ORIGIN
OBSREPOARCH_MASTERREPO
OBSREPOARCH_LOG_CONF
