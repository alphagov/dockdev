#!/usr/bin/env python
import sys, subprocess, os, json, argparse, git, docker, docker.utils, string, tempfile
from itertools import chain

class BuildDirectory:
  def __init__(self, service, path):
    self.service = service
    self.path = path
  
  def exists(self):
    return os.path.exists(self.path)
    
  def mkdir(self):
    if not self.exists():
      return os.makedirs(self.path)
  
  def clone_master(self):
    return git.Repo.clone_from(self.service.git_url, self.path)
  
  def checkout(self, commit_id):
    return git.Git(self.path).checkout(commit_id)
  
  def run_build(self, log_callback = None):
    if self.exists():
      script = os.path.join(self.path, "build-local.sh")
      log_callback("running {script}...".format(script=script))
      p = subprocess.Popen(script, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.path, bufsize=0)
      while True:
        line = p.stdout.readline()
        if line:
          if log_callback:
            log_callback(line.rstrip())
        else:
          break
      exit_code = p.wait()
      if exit_code != os.EX_OK:
        raise Exception("Stopped due to build error: {err}".format(err=exit_code))
    else:
      raise Exception("Build directory {path} does not exist".format(path=self.path))

class Service(object):
  def __init__(self, name, config):
    self.name = name
    self.docker_repo = config.get("docker_repo", None)
    self.git_url = config.get("git_repo", None)
    self.build_dir = config.get("build_dir", None)
    
  def get_head(self, branch):
    return git.Git().ls_remote(self.git_url, branch).split("\t")[0]
    
  def get_build_dir(self):
    return BuildDirectory(self, self.build_dir)
    
  def get_adhoc_dir(self):
    return BuildDirectory(self, tempfile.mkdtemp())

class DockDev:  
  def __init__(self):
    config_file_in_cwd = os.path.join(os.getcwd(), "config.json")
    config_file = os.environ.get("DOCKDEV_CONFIG", config_file_in_cwd)
    with open(config_file) as fp:
      self.services = parse_config(fp.read()) 
    kw = docker.utils.kwargs_from_env()
    if not kw:
      kw = {}
    kw["version"] = "1.20"
    if "tls" in kw:
      kw["tls"].assert_hostname = False
    self.client = docker.Client(**kw)
    
  def build(self, service, checkout):
    def log_callback(line):
      print "[{s.name}] {line}".format(s=service, line=line)
      
    build_dir = service.get_build_dir()
    if not build_dir.exists():
      if checkout:
          print "[{s.name}] cloning git repo {s.git_url} to {d.path}".format(s=service, d=build_dir)
          build_dir.mkdir()
          build_dir.clone_master()
      else:
        raise Exception ("{d.path} does not exist. Either checkout or run with -c.".format(d=build_dir))
    
    build_dir.run_build(log_callback)
    print "[{s.name}] {s.docker_repo}:local build successful".format(s=service)
    
  def adhoc(self, service, commit_id):
    def log_callback(line):
      print "[{s.name}] {line}".format(s=service, line=line)
    
    adhoc_dir = service.get_adhoc_dir()
    print "[{s.name}] cloning git repo {s.git_url} to {d.path}".format(s=service, d=adhoc_dir)
    adhoc_dir.clone_master()
    adhoc_dir.checkout(commit_id)
    adhoc_dir.run_build(log_callback)
    print "[{s.name}] {s.docker_repo}:adhoc build successful".format(s=service)
    
  def fetch(self, service, branches, adhoc = False):
    head = None
    for branch in branches:
      head = service.get_head(branch)
      if head:
        break
    
    if not head:
        raise Exception("No branches named {branches} found in {s.git_url}".format(
          s=service, branches=string.join(branches, ",")))    
    
    try:
      print "[{s.name}] {branch} HEAD is {head}".format(s=service, head=head, branch=branch)
      print "[{s.name}] fetching {s.docker_repo}:{head}".format(s=service, head=head)
      self.client.pull(service.docker_repo, tag=head)
      # successfully pulled? will throw Exception if not
      self.client.inspect_image(service.docker_repo + ":" + head)
      self.retag(service, head)
    except docker.errors.NotFound as e:
      if adhoc:
        print "[{s.name}] {s.docker_repo}:{head} not in registry, doing adhoc build".format(s=service, head=head)
        self.adhoc(service, commit_id = head)
      else:
        raise e
        
  def retag(self, service, tag):
    print "[{s.name}] tagging {s.docker_repo}:{tag} as {s.docker_repo}:local".format(s=service, tag=tag)
    self.client.tag(service.docker_repo + ":" + tag, service.docker_repo, "local", True)

def parse_config(config_data):
  config_json = json.loads(config_data)
  services = []
  for name, config in config_json["services"].iteritems():
    merged_config = config_json.get("template", {})
    merged_config.update(config)
    merged_config = {k: os.path.expandvars(v.format(name=name)) for k, v in merged_config.iteritems()}
    services.append(Service(name, merged_config))
  return services

def parse_args(argv):
  parser = argparse.ArgumentParser(
    usage="Fetches and/or builds docker images for services and tags them with :local in your machine's docker. You " +
      "can then use them in scenarios like docker-compose to start an app comprised of multiple services. Default is " +
      "fetching master images from the registry, but can also fetch named branches or build locally with any changes. ")
  parser.add_argument("-l", "--local", default=[], action="append", nargs=1,
    metavar="APP[,APP[,...]]", help="Build service image for local git checkout (inc. changes)")
  parser.add_argument("-b", "--branch", default=[], action="append", nargs=2,
    metavar=("BRANCH", "APP[,APP[,...]]"), help="Fetch service image for built for branch")
  parser.add_argument("-r", "--retag", default=[], action="append", nargs=2,
    metavar=("TAG", "APP[,APP[,...]]"), help="Retag existing service image with local tag")
  parser.add_argument("-o", "--only", default=False, action="store_true",
    help="Turns off default branch fetch. Only build services explicitly specified in options.")
  parser.add_argument("-d", "--default", default=[], action="append", nargs=1,
    metavar="BRANCH[,BRANCH[,...]]", help="Change the default branch to be fetched to something other than master for" + 
      "projects not specifically enumerated in -l or -b. Specify comma separated list to try each branches until one " +
      "is found (useful for working with branches of the same name together across some but not all services).")
  parser.add_argument("-c", "--checkout", default=False, action="store_true",
    help="Enable automatic checkout of services in -l if not currently present in build dir.")
  parser.add_argument("-a", "--adhoc", default=False, action="store_true",
    help="Attempt to checkout & build branches that would otherwise be fetched when no image is in the registry.")
    
  parsed_args = parser.parse_args(argv)
  local = set(chain(*[x[0].split(",") for x in parsed_args.local]))
  branch = dict(chain(*map(lambda e : [(key, e[0]) for key in e[1].split(",")], parsed_args.branch)))
  retag = dict(chain(*map(lambda e : [(key, e[0]) for key in e[1].split(",")], parsed_args.retag)))
  default = list(chain(*[x[0].split(",") for x in parsed_args.default]))
  
  return (local, branch, retag, default, parsed_args.checkout, parsed_args.adhoc, parsed_args.only)

def main(argv):
  dockdev = DockDev()
  (local, branch, retag, default, checkout, adhoc, only) = parse_args(argv)
  if len(default) == 0:
    default = ["master"]
  
  print "----------------------------------------"
  for service in dockdev.services:
    if service.name in local:
      dockdev.build(service, checkout)
    elif service.name in retag:
      dockdev.retag(service, retag[service.name])
    elif service.name in branch:
      dockdev.fetch(service, branch[service.name], adhoc)
    elif not only:
      dockdev.fetch(service, default, adhoc)
    else:
      print "[{s.name}] skipped".format(s=service)
    print "----------------------------------------"