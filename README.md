# DockDev

DockDev is a development environment tool that helps with applications composed of multiple docker images that need to be run together as an application.

## Technical Documentation

DockDev works by applying a `:local` tag to whatever docker build the developer wishes to use. These may be images pulled from a docker registry, or built locally, in whatever mix is appropriate for development of a feature - since not all features will impact all services. 

You can build a `docker-compose.yml` or similar file that links together images with these `:local` tags, or just run using some scripts.

### Usage

As a developer, DockDev can be used to mix clean, pre-built master or branch images with ones checked out locally that, for example, contain work on features.

DockDev is available in PyPI. You can install it using pip (may need to sudo on some platforms):

```
pip install dockdev
```

Run `dockdev` in the directory your `config.json` is located. See below on how `config.json` should look (it's something you'll build once as a team and will probably be stored in your repositories ready to be checked out). Default behaviour is to fetch *master* images for everything configured in `config.json`. Specifying options to `dockdev` changes its behaviour:

Examples:
* `dockdev` - fetches the *master* image from the registry for all services and tags them with `:local`.
* `dockdev -l service1 -c` - fetches *master* image for everything except *service1*. Checks out the code for *service1*, builds it using the `Dockerfile` via `build-local.sh`. 
* `dockdev -l service1` - fetches *master* image for everything except *service1*. Builds existing checked out code for *service1* using the `Dockerfile` via `build-local.sh`. 
* `dockdev -l service1 -l service2`  - fetches *master* image for everything except *service1* and *service2*. Builds checked out code for *service1* and *service2* using the `Dockerfile` via `build-local.sh`. 
* `dockdev -b <branch1> service1` - fetches *master* image for everything except *service1*. Fetches *branch1* image for *service1*.
* `dockdev -b <branch1> service1 -b branch2 service2 -l service3` - A combination of branch and local builds as above. You can combine as many options as you want.
* `dockdev -b <branch1> service1,service2` - alternative syntax for *service1* and *service2* both on *branch1*.

### Dependencies

Each ‘service’ in DockDev must follow a pattern comprised of the following elements:

Its own source code repository in git.
A repository in DockerHub or similar docker registry.
A Dockerfile to packages and runs the source code, e.g.:

```
FROM java:8-jre
ENV JAVA_HOME /usr/lib/jvm/java-8-*/
EXPOSE 8080
WORKDIR /app
ADD target/packaged.jar /app/
CMD java -jar packaged.jar 8080
```

A `build-local.sh` also in the root that builds a docker image and tags it with the repository name but a `:local` tag (which is never pushed):

```
#!/bin/bash
mvn -DskipTests package && docker build -t repo/project:local .
```

A CI server (or other means, such as a commit hook) that produces docker images for master and other branches when people commit to them, and pushing them to the registry tagged with their SHA1 commit ID, e.g. 

```
reponame/project:d670460b4b4aece5915caf5c68d12f560a9fe3e4
```

Recommended: `docker-compose` used to set up services to run together, everything referencing images with a :local tag, linked together using docker links.

You’ll need to produce a `config.json` listing your services describing your services. It should look like the following:

```json
{
  "services": {
    "service1" : {
      "git_repo": "git@git:orgname/service1.git", 
      "docker_repo": "registryorg/service1", 
      "build_dir": "$WORKSPACE/service1"
    },
    "service2" : {
      "git_repo": "git@git:orgname/service2.git",
      "docker_repo": "registryorg/service2", 
      "build_dir": "$WORKSPACE/service2"
    },
    "service3" : {
      "git_repo": "git@git:orgname/service2.git",
      "docker_repo": "registryorg/service3", 
      "build_dir": "$WORKSPACE/service3"
    }
  }
}
```

As you might expect:

 * `git_repo` is the location of the service's repo in git.
 * `docker_repo` is the location of the service's docker registry repository.
 * `build_dir` is where checked out code lives.

All values will have environment variables interpolated to make life easier. In the above example we use `$WORKSPACE` which developers will set to where they'd like the services code to live. DockDev will also do a string interpolation for `{name}` to make things potentially more formulaic.

### Running Tests

Create a virtual environment and install dependencies:

```
virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

Tests themselves are run with nose:

```
nosetests
```

## Licence

[MIT License](LICENCE)
