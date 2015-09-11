#!/usr/bin/env python

from dockdev.dockdev import parse_args

from nose.tools import assert_equal
from nose.tools import assert_not_equal
from nose.tools import assert_raises
from nose.tools import assert_in
from nose.tools import raises

class TestArguments(object):
    def test_defaults(self):
        (local, branch, retag, default, checkout, adhoc, only) = parse_args([])

        assert_equal({}, branch)
        assert_equal(0, len(local))
        assert_equal(False, only)        
        assert_equal(False, checkout)
        
    def test_local(self):
        (local, branch, retag, default, checkout, adhoc, only) = parse_args(['-l', 'service1'])

        assert_equal({}, branch)
        assert_in('service1', local)
        assert_equal(False, only)        
        assert_equal(False, checkout)
        
    def test_local_multi(self):
        (local, branch, retag, default, checkout, adhoc, only) = parse_args(['-l', 'service1', '-l', 'service2'])

        assert_equal({}, branch)
        assert_in('service1', local)
        assert_in('service2', local)
        assert_equal(False, only)        
        assert_equal(False, checkout)
        
    def test_local_multi_alt(self):
        (local, branch, retag, default, checkout, adhoc, only) = parse_args(['-l', 'service1,service2'])

        assert_equal({}, branch)
        assert_in('service1', local)
        assert_in('service2', local)
        assert_equal(False, only)        
        assert_equal(False, checkout)
        
    def test_local_multi_combo(self):
        (local, branch, retag, default, checkout, adhoc, only) = parse_args(['-l', 'service1,service2', '-l', 'service3'])

        assert_equal({}, branch)
        assert_in('service1', local)
        assert_in('service2', local)
        assert_in('service3', local)
        assert_equal(False, only)        
        assert_equal(False, checkout)
        
    def test_branch(self):
        (local, branch, retag, default, checkout, adhoc, only) = parse_args(['-b', 'branch1', 'service1'])

        assert_equal('branch1', branch['service1'])
        assert_equal(0, len(local))
        assert_equal(only, False)        
        assert_equal(checkout, False)
        
    def test_branch_multi(self):
        (local, branch, retag, default, checkout, adhoc, only) = parse_args(['-b', 'branchA', 'service1,service2'])

        assert_equal('branchA', branch['service1'])
        assert_equal('branchA', branch['service2'])
        assert_equal(0, len(local))
        assert_equal(only, False)        
        assert_equal(checkout, False)
        
    def test_branch_multi_diff(self):
        (local, branch, retag, default, checkout, adhoc, only) = parse_args(['-b', 'branchA', 'service1', '-b', 'branchB', 'service2'])

        assert_equal('branchA', branch['service1'])
        assert_equal('branchB', branch['service2'])
        assert_equal(0, len(local))
        assert_equal(only, False)        
        assert_equal(checkout, False)
        
    def test_only(self):
        (local, branch, retag, default, checkout, adhoc, only) = parse_args(['-o'])

        assert_equal({}, branch)
        assert_equal(0, len(local))
        assert_equal(True, only)        
        assert_equal(False, checkout)
        
    def test_checkout(self):
        (local, branch, retag, default, checkout, adhoc, only) = parse_args(['-c'])

        assert_equal({}, branch)
        assert_equal(0, len(local))
        assert_equal(False, only)        
        assert_equal(True, checkout)
        
    def test_combo(self):
        (local, branch, retag, default, checkout, adhoc, only) = parse_args(['-l', 'service1', '-b', 'branchA', 'service2', '-c'])

        assert_equal('branchA', branch['service2'])
        assert_in('service1', local)
        assert_equal(only, False)        
        assert_equal(checkout, True)
        
    def test_default(self):
        (local, branch, retag, default, checkout, adhoc, only) = parse_args(['-d', 'master'])
        assert_equal(['master'], default)
        
    def test_default_csl(self):
        (local, branch, retag, default, checkout, adhoc, only) = parse_args(['-d', 'branchA,master'])
        assert_equal(['branchA', 'master'], default)
        
    def test_adhoc(self):
        (local, branch, retag, default, checkout, adhoc, only) = parse_args(['-a'])
        assert_equal(True, adhoc)
