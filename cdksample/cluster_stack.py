from aws_cdk import (
    core,
    aws_ecs as ecs
)


class ClusterStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, props, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        vpc = props['vpc']

        # ECSクラスターの作成
        # https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ecs.README.html#clusters
        # https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ecs/Cluster.html

        cluster = ecs.Cluster(
            self, 'Cluster',
            vpc=vpc
        )

        cluster.add_default_cloud_map_namespace(
            name=self.node.try_get_context('namespace')
        )

        self.output_props = props.copy()
        self.output_props['cluster'] = cluster

    @property
    def outputs(self):
        return self.output_props
