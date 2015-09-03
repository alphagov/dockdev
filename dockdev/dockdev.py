#!/usr/bin/env python
import sys, subprocess, os, json, argparse, itertools, git, docker, docker.utils

def get_docker():
  kw = docker.utils.kwargs_from_env()
  if kw and 'tls' in kw:
    kw['tls'].assert_hostname = False
  return docker.Client(**kw)
  
def get_git():
  return git.Git()
  
def get_config():
  config_file = os.path.join(os.getcwd(), "config.json")
  with open(config_file) as fp:
    return parse_config(fp.read())

def parse_config(config):
  config_json = json.loads(config)
  services = []
  for name, config in config_json["services"].iteritems():
    merged_config = config_json.get("template", {})
    merged_config.update(config)
    merged_config = {k: os.path.expandvars(v.format(name=name)) for k, v in merged_config.iteritems()}
    services.append(Service(name, merged_config))
  return services

def get_value(config, key):
  return config.get("docker_repo", template.get("docker_repo", None))

class Service(object):
  def __init__(self, name, config):
    self.name = name
    self.docker_repo = config.get("docker_repo", None)
    self.git_repo = config.get("git_repo", None)
    self.build_dir = config.get("build_dir", None)
    
  def build(self, git, auto_checkout):
    if not os.path.exists(self.build_dir):
      if auto_checkout:
        print "[{s.name}] cloning git repo {s.git_repo} to {s.build_dir}".format(s=self)
        git.clone(self.git_repo, self.build_dir)
      else:
        raise Exception ("{s.build_dir} does not exist. Either checkout or run with -c.".format(s=self))
    
    build_script = os.path.join(self.build_dir, "build-local.sh")
    print "[{s.name}] Building using {script}...".format(s=self, script=build_script)
    p = subprocess.Popen(build_script, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.build_dir, bufsize=0)
    while True:
      line = p.stdout.readline()
      if line != '':
        print "[{s.name}] {line}".format(s=self, line=line.rstrip())
      else:
        break
    exit_code = p.wait()
    if exit_code != os.EX_OK:
      raise Exception("Stopped due to build error: {err}".format(err=exit_code))
      
    print "[{s.name}] {s.docker_repo}:local build successful".format(s=self)
  
  def fetch(self, branch, docker):
    head = git.Git().ls_remote(self.git_repo, branch).split("\t")[0]
    if not head:
      raise Exception("Branch {branch} not found in {s.git_repo}".format(s=self, branch=branch))
    
    print "[{s.name}] {branch} HEAD is {head}".format(s=self, head=head, branch=branch)
    print "[{s.name}] fetching {s.docker_repo}:{head}".format(s=self, head=head)
    docker.pull(self.docker_repo, tag=head)
    self.retag(head, docker)

  def retag(self, tag, docker):
    print "[{s.name}] tagging {s.docker_repo}:{tag} as {s.docker_repo}:local".format(s=self, tag=tag)
    docker.tag(self.docker_repo + ":" + tag, self.docker_repo, "local", True)

def parse_args(argv):
  parser = argparse.ArgumentParser(
    usage="Fetches and/or builds docker images for services and tags them with :local in your machine's docker. You " +
      "can then use them in scenarios like docker-compose to start an app comprised of multiple services. Default is " +
      "fetching master images from the registry, but can also fetch named branches or build locally with any changes. ")
  parser.add_argument('-l', '--local', default=[], action='append', nargs=1,
    metavar="APP[,APP[,...]]", help="Build service image for local git checkout (inc. changes)")
  parser.add_argument('-b', '--branch', default=[], action='append', nargs=2,
    metavar=("BRANCH", "APP[,APP[,...]]"), help="Fetch service image for built for branch")
  parser.add_argument('-r', '--retag', default=[], action='append', nargs=2,
    metavar=("TAG", "APP[,APP[,...]]"), help="Retag existing service image with local tag")
  parser.add_argument('-o', '--only', default=False, action='store_true',
    help="Turns off default master fetch. Only build services explicitly specified in options.")
  parser.add_argument('-c', '--checkout', default=False, action='store_true',
    help="Enable automatic checkout of services if not currently present in build dir.") 
    
  parsed_args = parser.parse_args(argv)
  local = set(itertools.chain(*[x[0].split(',') for x in parsed_args.local]))
  branch = dict(itertools.chain(*map(lambda e : [(key, e[0]) for key in e[1].split(',')], parsed_args.branch)))
  retag = dict(itertools.chain(*map(lambda e : [(key, e[0]) for key in e[1].split(',')], parsed_args.retag)))
  
  return (local, branch, retag, parsed_args.checkout, parsed_args.only)

def main(argv):
  docker = get_docker()
  git = get_git()
  (local, branch, retag, auto_checkout, only) = parse_args(argv)
  
  print "----------------------------------------"
  for service in get_config():
    if service.name in local:
      service.build(git, auto_checkout)
    elif service.name in branch:
      service.fetch(branch[service.name], docker)
    elif service.name in retag:
      service.retag(retag[service.name], docker)
    elif not only:
      service.fetch("master", docker)
    else:
      print "[{s.name}] skipped".format(s=service)
    print "----------------------------------------"