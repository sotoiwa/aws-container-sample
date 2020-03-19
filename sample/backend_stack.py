from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_iam as iam
)


class BackendStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, props, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        table_name = self.node.try_get_context('table_name')
        vpc = props['vpc']
        endpoint_sg = props['endpoint_sg']
        cluster = props['cluster']
        frontend_service = props['frontend_service']

        # タスク実行ロールの作成
        task_execution_role_policy = iam.ManagedPolicy.from_aws_managed_policy_name(
            'service-role/AmazonECSTaskExecutionRolePolicy')
        task_execution_role = iam.Role(
            self, 'TaskExecutionRole',
            assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
            managed_policies=[task_execution_role_policy]
        )

        # タスクロールの作成
        task_role_policy = iam.ManagedPolicy.from_aws_managed_policy_name(
            'AmazonDynamoDBFullAccess'
        )
        task_role = iam.Role(
            self, 'TaskRole',
            assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
            managed_policies=[task_role_policy]
        )

        # リポジトリを指定する
        repository = ecr.Repository.from_repository_name(
            self, 'Backend', 'backend'
        )

        # タスク定義の作成
        # https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ecs.README.html#task-definitions
        # https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ecs/FargateTaskDefinition.html

        task_definition = ecs.FargateTaskDefinition(
            self, 'TaskDef',
            memory_limit_mib=512,
            cpu=256,
            execution_role=task_execution_role,
            task_role=task_role
        )
        container = task_definition.add_container(
            'Container',
            image=ecs.ContainerImage.from_ecr_repository(
                repository=repository,
                tag='latest'
            ),
            logging=ecs.AwsLogDriver(
                stream_prefix='/ecs/'
            ),
            environment={
                'DYNAMODB_TABLE_NAME': table_name
            }
        )
        container.add_port_mappings(
            ecs.PortMapping(container_port=5000)
        )

        # Backendサービス用セキュリティーグループ
        backend_service_sg = ec2.SecurityGroup(
            self, 'BackendServiceSecurityGroup',
            vpc=vpc
        )

        # サービスの作成
        # https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ecs.README.html#service
        # https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ecs.html

        backend_service = ecs.FargateService(
            self, 'BackendService',
            cluster=cluster,
            task_definition=task_definition,
            desired_count=2,
            min_healthy_percent=50,
            max_healthy_percent=200,
            security_group=backend_service_sg,
            cloud_map_options=ecs.CloudMapOptions(
                name='backend'
            )
        )

        # Frontendサービスからのトラフィックを許可
        backend_service.connections.allow_from(
            frontend_service,
            ec2.Port.all_traffic()
        )
        # 自身のセキュリティーグループからのトラフィックを許可
        backend_service.connections.allow_internally(
            ec2.Port.all_traffic()
        )
        # エンドポイントのセキュリティーグループへのアクセスを許可
        backend_service.connections.allow_to(
            endpoint_sg,
            ec2.Port.all_traffic()
        )

        self.output_props = props.copy()

    @property
    def outputs(self):
        return self.output_props
