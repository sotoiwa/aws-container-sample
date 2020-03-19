#!/usr/bin/env python3

from aws_cdk import core

from sample.network_stack import NetworkStack
from sample.dynamodb_stack import DynamoDbStack
from sample.cluster_stack import ClusterStack
from sample.frontend_stack import FrontendStack
from sample.backend_stack import BackendStack

# スタック間のデータの受け渡しは以下を参考
# https://github.com/aws-samples/aws-cdk-examples/tree/master/python/codepipeline-docker-build

app = core.App()

props = dict()
prefix = app.node.try_get_context('stack_prefix')
props['prefix'] = prefix
env = core.Environment(
    region=app.node.try_get_context('region')
)

vpc_stack = NetworkStack(app, '{}-NetworkStack'.format(prefix), env=env, props=props)
dynamodb_stack = DynamoDbStack(app, '{}-DynamoDbStack'.format(prefix), env=env, props=vpc_stack.outputs)
cluster_stack = ClusterStack(app, '{}-ClusterStack'.format(prefix), env=env, props=vpc_stack.outputs)
frontend_stack = FrontendStack(app, '{}-FrontendStack'.format(prefix), env=env, props=cluster_stack.outputs)
backend_stack = BackendStack(app, '{}-BackendStack'.format(prefix), env=env, props=frontend_stack.outputs)

app.synth()
