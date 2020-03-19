from aws_cdk import (
    core,
    aws_dynamodb as dynamodb
)


class DynamoDbStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, props, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        table_name = self.node.try_get_context('table_name')

        table = dynamodb.Table(
            self, 'Table',
            table_name=table_name,
            partition_key=dynamodb.Attribute(
                name='uuid', type=dynamodb.AttributeType.STRING
            ),
            read_capacity=1,
            write_capacity=1,
            removal_policy=core.RemovalPolicy.DESTROY
        )
        self.output_props = props.copy()

    @property
    def outputs(self):
        return self.output_props
