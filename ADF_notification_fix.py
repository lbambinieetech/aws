class Notifications(core.Construct):
    def __init__(
        self, scope: core.Construct, id: str, map_params: dict, **kwargs
    ):  # pylint: disable=W0622
        super().__init__(scope, id, **kwargs)
        LOGGER.debug("Notification configuration required for %s", map_params["name"])
        # pylint: disable=no-value-for-parameter
        _slack_func = _lambda.Function.from_function_arn(
            self,
            "slack_lambda_function",
            "arn:aws:lambda:{0}:{1}:function:SendSlackNotification".format(
                ADF_DEPLOYMENT_REGION, ADF_DEPLOYMENT_ACCOUNT_ID
            ),
        )
        _topic = _sns.Topic(self, "PipelineTopic")
        _statement = _iam.PolicyStatement(
            actions=["sns:Publish"],
            effect=_iam.Effect.ALLOW,
            principals=[
                _iam.ServicePrincipal("sns.amazonaws.com"),
                _iam.ServicePrincipal("codecommit.amazonaws.com"),
                _iam.ServicePrincipal("events.amazonaws.com"),
            ],
            resources=["*"],
        )
        _topic.add_to_resource_policy(_statement)
        _endpoint = map_params.get("params", {}).get("notification_endpoint", "")
        _sub = _sns.Subscription(
            self,
            "sns_subscription",
            topic=_topic,
            endpoint=_endpoint if "@" in _endpoint else _slack_func.function_arn,
            protocol=_sns.SubscriptionProtocol.EMAIL
            if "@" in _endpoint
            else _sns.SubscriptionProtocol.LAMBDA,
        )
        if "@" not in _endpoint:
            _lambda.CfnPermission(
                self,
                "slack_notification_sns_permissions",
                principal="sns.amazonaws.com",
                action="lambda:InvokeFunction",
                source_arn=_topic.topic_arn,
                function_name="SendSlackNotification",
            )
            _slack_func.add_event_source(source=_event_sources.SnsEventSource(_topic))
        self.topic_arn = _topic.topic_arn
