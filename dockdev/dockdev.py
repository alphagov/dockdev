#!/usr/bin/env python
import sys, subprocess, os, json, argparse, itertools, git, docker, docker.utils, docker.errors

def docker_args():
  kw = docker.utils.kwargs_from_env()
  if kw and 'tls' in kw:
    kw['tls'].assert_hostname = False
  return kw
  
docker_client = docker.Client(**docker_args())

def get_config():
  config_file = os.path.join(os.getcwd(), 'config.json')
  with open(config_file) as fp:
    return json.loads(fp.read())

def get_commit(repo, branch):
  commit = git.Git().ls_remote(repo, branch).split("\t")[0]
  if commit == '':
    raise Exception("Branch %s not found in %s" % (branch, repo))
  return commit
  
def fetch_image(config, app, branch):
  repo = config['hub'] % app
  head = get_commit(config["git"] % app, branch)
  
  print "[%s] %s HEAD is %s, fetching %s:%s" % (app, branch, head, repo, head)
  docker_client.pull(repo, tag=head)
  
  print "[%s] tagging %s:%s as %s:local" % (app, repo, head, repo)
  docker_client.tag(repo + ":" + head, repo, "local", True)
  
def build_image(config, app):
  repo = config['hub'] % app
  script_dir = os.path.expandvars(config['dir'] % app)
  script = os.path.join(script_dir, "build-local.sh")
  
  print "[%s] Building using %s..." % (app, script)
  p = subprocess.Popen(script, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd = script_dir, bufsize = 0)
  while True:
    line = p.stdout.readline()
    if line != '':
      print "[%s] %s" % (app, line.rstrip())
    else:
      break
  exit_code = p.wait()
  if exit_code != os.EX_OK:
    raise Exception("Stopped due to error: %s" % (app, str(exit_code)))
  
  print "[%s] $s:local build finished" % (app, local_id)

def main(argv):
  parser = argparse.ArgumentParser(
    usage="Fetches or builds docker images for microservices and tags them with :local in " +
          "your running docker instance so docker-compose will use them when spinning up a " +
          "development environment. Defaults to fetching master images from DockerHub, can " +
          "also fetch particular branches or build checked out source with the following " +
          "options.")
  parser.add_argument('-l', '--local', default=[], action='append', nargs=1,
    metavar="APP[,APP[,...]]", help="Build app image for local git checkout (inc. changes)")
  parser.add_argument('-b', '--branch', default=[], action='append', nargs=2,
    metavar=("BRANCH", "APP[,APP[,...]]"), help="Fetch app image for built for branch")
  parser.add_argument('-o', '--only', default=False, action='store_true',
    help="Turns off default master fetch. Only build apps explicitly specified in options.")

  args = parser.parse_args(argv)
  config = get_config()
  local = set(itertools.chain(*[x[0].split(',') for x in args.local]))
  branch = dict(itertools.chain(*map(lambda e : [(key, e[0]) for key in e[1].split(',')], args.branch)))
  only = args.only

  for app in config['apps']:
    if app in local:
      build_image(config, app)
    elif app in branch:
      fetch_image(config, app, branch[app])
    elif not only:
      fetch_image(config, app, 'master')
    else:
      print "[%s] skipped" % app
    print "----------------------------------------"

if __name__ == "__main__":
  try:
    main(sys.argv[1:])
  except KeyboardInterrupt as e:
    print "Aborted"
  except Exception as e:
    print "ERROR: %s" % str(e)