from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam
)


class FrontendStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, props, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        vpc = props['vpc']
        endpoint_sg = props['endpoint_sg']
        cluster = props['cluster']

        # タスク実行ロールの作成
        task_execution_role_policy = iam.ManagedPolicy.from_aws_managed_policy_name(
            'service-role/AmazonECSTaskExecutionRolePolicy')
        task_execution_role = iam.Role(
            self, 'TaskExecutionRole',
            assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
            managed_policies=[task_execution_role_policy]
        )

        # タスクロールの作成
        task_role = iam.Role(
            self, 'TaskRole',
            assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com')
        )

        # リポジトリを指定する
        repository = ecr.Repository.from_repository_name(
            self, 'Frontend', 'frontend'
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
                'BACKEND_URL': 'http://backend.mycluster.local:5000/messages'
            }
        )
        container.add_port_mappings(
            ecs.PortMapping(container_port=5000)
        )

        # ALB用セキュリティーグループ
        alb_sg = ec2.SecurityGroup(
            self, 'ALBSecurityGroup',
            vpc=vpc
        )

        # ALBを作成
        alb = elbv2.ApplicationLoadBalancer(
            self, 'ALB',
            vpc=vpc,
            internet_facing=True,
            security_group=alb_sg
        )

        # # 80番ポートへのトラフィックを許可
        # alb_sg.add_ingress_rule(
        #     peer=ec2.Peer.any_ipv4(),
        #     connection=ec2.Port.tcp(80)
        # )
        alb.connections.allow_from_any_ipv4(
            ec2.Port.tcp(80)
        )

        # Frontendサービス用セキュリティーグループ
        frontend_service_sg = ec2.SecurityGroup(
            self, 'FrontendServiceSecurityGroup',
            vpc=vpc
        )

        # サービスの作成
        # https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ecs.README.html#service
        # https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ecs.html

        frontend_service = ecs.FargateService(
            self, 'FrontendService',
            cluster=cluster,
            task_definition=task_definition,
            min_healthy_percent=50,
            max_healthy_percent=200,
            desired_count=2,
            security_group=frontend_service_sg,
            cloud_map_options=ecs.CloudMapOptions(
                name='frontend'
            )
        )

        # ALB用セキュリティグループからのトラフィックを許可
        frontend_service.connections.allow_from(
            alb,
            ec2.Port.all_traffic()
        )
        # 自身のセキュリティグループからのトラフィックを許可
        frontend_service.connections.allow_internally(
            ec2.Port.all_traffic()
        )
        # エンドポイントのセキュリティグループへのアクセスを許可
        frontend_service.connections.allow_to(
            endpoint_sg,
            ec2.Port.all_traffic()
        )

        # ApplicationLister
        # https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_elasticloadbalancingv2/ApplicationListener.html#aws_cdk.aws_elasticloadbalancingv2.ApplicationListener

        listener = alb.add_listener(
            'Listener',
            port=80
        )

        listener.add_targets(
            'ECS',
            port=5000,
            protocol=elbv2.ApplicationProtocol.HTTP,
            targets=[frontend_service],
            health_check=elbv2.HealthCheck(
                path='/health',
                interval=core.Duration.seconds(10),
                healthy_threshold_count=2
            )
        )

        core.CfnOutput(
            self, 'LoadBalancerDNS',
            description='Load Balancer DNS Name',
            value=alb.load_balancer_dns_name
        )

        self.output_props = props.copy()
        self.output_props['frontend_service'] = frontend_service

    @property
    def outputs(self):
        return self.output_props
