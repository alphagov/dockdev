#!/usr/bin/env python

from dockdev.dockdev import parse_config

import os

from nose.tools import assert_equal
from nose.tools import assert_not_equal
from nose.tools import assert_raises
from nose.tools import assert_in
from nose.tools import raises

class TestConfig(object):
    def test_empty(self):
        parse_config('{ "services": {} }')
        
    def test_basic(self):
        services = parse_config('{ "services": { "service1": { "git_repo": "abc", "docker_repo": "def", "build_dir": "ghi" } } }')
        assert_equal(1, len(services))
        assert_equal("service1", services[0].name)
        assert_equal("abc", services[0].git_repo)
        assert_equal("def", services[0].docker_repo)
        assert_equal("ghi", services[0].build_dir)
        
    def test_two(self):
        services = parse_config('{ "services": { ' + 
          '"service1": { "git_repo": "abc", "docker_repo": "def", "build_dir": "ghi" }, ' + 
          '"service2": { "git_repo": "123", "docker_repo": "456", "build_dir": "789" } ' + 
        '} }')
        
        assert_equal(2, len(services))
        
        assert_equal("service1", services[1].name)
        assert_equal("abc", services[1].git_repo)
        assert_equal("def", services[1].docker_repo)
        assert_equal("ghi", services[1].build_dir)

        assert_equal("service2", services[0].name)
        assert_equal("123", services[0].git_repo)
        assert_equal("456", services[0].docker_repo)
        assert_equal("789", services[0].build_dir)
        
    def test_name_replacement(self):
        services = parse_config('{ "services": { "service1": { "git_repo": "{name}.git", "docker_repo": "def", "build_dir": "ghi" } } }')
        assert_equal(1, len(services))
        assert_equal("service1.git", services[0].git_repo)
        
    def test_env_replacement(self):
        os.environ['JUST_FOR_TESTING'] = 'TESTING'
        services = parse_config('{ "services": { "service1": { "git_repo": "abc", "docker_repo": "def", "build_dir": "$JUST_FOR_TESTING/foo" } } }')
        assert_equal(1, len(services))
        assert_equal("TESTING/foo", services[0].build_dir)
        
    def test_template(self):
        services = parse_config('{ "template": { "git_repo": "abc", "docker_repo": "def", "build_dir": "ghi" }, "services" : { "service1": {}, "service2" : {} } }')
        
        assert_equal(2, len(services))
        assert_equal("service2", services[0].name)
        assert_equal("abc", services[0].git_repo)
        assert_equal("def", services[0].docker_repo)
        assert_equal("ghi", services[0].build_dir)
        
        assert_equal("service1", services[1].name)
        assert_equal("abc", services[1].git_repo)
        assert_equal("def", services[1].docker_repo)
        assert_equal("ghi", services[1].build_dir)
        
    def test_template_name_replacement(self):
        services = parse_config('{ "template": { "git_repo": "{name}.git", "docker_repo": "def", "build_dir": "ghi" }, "services" : { "service1": {} } }')
        
        assert_equal(1, len(services))
        assert_equal("service1", services[0].name)
        assert_equal("service1.git", services[0].git_repo)

    def test_template_override(self):
        services = parse_config('{ "template": { "git_repo": "abc", "docker_repo": "def", "build_dir": "ghi" }, "services" : { "service1": { "git_repo": "123" } } }')
        
        assert_equal(1, len(services))
        assert_equal("123", services[0].git_repo)