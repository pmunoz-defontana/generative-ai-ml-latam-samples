import json
from aws_cdk import (
    # Duration,
    Stack,
    aws_iam as iam,
    # aws_sqs as sqs,
)
from constructs import Construct


DEFAULT_MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
from bedrock_agent import Agent, ActionGroup
from lambdas import Lambdas
from databases import Tables


class MultiAgentCollaborationStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Tables and Lambda functions,  set up permissions and environment variables
        self._create_and_configure_resources()

        # Create agents: support, orders and supervisor
        self._create_agents()

        self.supervisor_agent.enable_collaboration(how="SUPERVISOR_ROUTER") # SUPERVISOR / SUPERVISOR_ROUTER / DISABLED

        self.supervisor_agent.add_collaborator(
            self.support_agent.alias,
            "support-tickets",
            "Use this agent when you need to create a customer support ticket or get ticket status, use this before escalation.  \
            You can only create tickets and inform status. ",
        )

        self.supervisor_agent.add_collaborator(
            self.orders_agent.alias,
            "orders",
            "Use this agent when you need to get the customer's order information",
        )

        self.supervisor_agent.add_collaborator(
            self.escalation_agent.alias,
            "escalation",
            "Escalates to human, for issues no being solved with a ticket.",
        )

        self.supervisor_agent.prepare_agent()

    def _create_and_configure_resources(self) -> None:

        # Create resources
        self.tables = Tables(self, "Tb")
        self.functions = Lambdas(self, "Fn")

        # Grant permissions
        self.tables.orders.grant_read_data(self.functions.orders)
        self.tables.tickets.grant_read_write_data(self.functions.tickets)

        # Set environment variables
        self.functions.orders.add_environment(
            "ORDER_TABLE_NAME", self.tables.orders.table_name
        )
        self.functions.tickets.add_environment(
            "TICKET_TABLE_NAME", self.tables.tickets.table_name
        )

        # Grant Bedrock permissions
        bedrock_principal = iam.ServicePrincipal("bedrock.amazonaws.com")
        self.functions.orders.grant_invoke(bedrock_principal)
        self.functions.tickets.grant_invoke(bedrock_principal)

    def _create_agents(self) -> None:

        support_action_groups = ActionGroup().from_file(
            "agent_action_group_support_data.json", self.functions.tickets
        )

        # Create support agent
        self.support_agent = Agent(
            self,
            "SupportAgent",
            action_groups=support_action_groups,
            agent_name="mac-ticket",
            agent_description="Ticket Support",
            agent_instruction=(
                "Usted es un amable agente de soporte a cliente que ayuda creando tickets y entregando informacion de tickets de atencion de postventa."
            ),
            foundation_model=DEFAULT_MODEL_ID,
        )
        self.support_agent.create_alias("mac-ticket-alias")

        # Create orders agent
        order_action_groups = ActionGroup().from_file(
            "agent_action_group_order_data.json", self.functions.orders
        )
        self.orders_agent = Agent(
            self,
            "OrdersAgent",
            action_groups=order_action_groups,
            agent_name="mac-orders",
            agent_description="Order Information",
            agent_instruction=(
                "Usted es un amable agente que maneja los pedidos de los clientes y entrega informacion sobre los pedidos."
            ),
            foundation_model=DEFAULT_MODEL_ID,
        )
        self.orders_agent.create_alias("mac-orders-alias")


        # Create escalating agent
        escalating_action_groups = ActionGroup().from_file("agent_action_group_escalation_data.json")
        self.escalation_agent = Agent(
            self,
            "Escalating",
            action_groups=escalating_action_groups,
            agent_name="mac-escalation",
            agent_description="Escalation",
            agent_instruction=(
                "Usted es un amable agente que es capaz de escalar casos de cliente a las áreas especialistas"
            ),
            foundation_model=DEFAULT_MODEL_ID,
        )
        self.escalation_agent.create_alias("mac-orders-alias")


        # Create supervisor agent
        supervisor_action_groups = ActionGroup().from_file(
            "agent_action_group_supervisor_data.json"
        )
        self.supervisor_agent = Agent(
            self,
            "SupervisorAgent",
            action_groups=supervisor_action_groups,
            agent_name="mac-supervisor",
            agent_description="Agente de primera linea puede manejar tickers, estado de pedidos y escalamientos",
            agent_instruction=(
                "Usted es un amable Agente de primera linea que puede manejar tickets de soporte, estado de pedidos y escalamientos a personas especialistas. \
                1) si el cliente necesita conocer el estado del pedido puede buscar y entregar esa informacion.\
                2) si el cliente tiene un problema con su pedido primero crea un ticket. \
                3) si ya ha creado un ticket puede entregar el estado del ticket.\
                4) si el ticket no es suficiente, puede escalar a un agente humano para que vea el caso."
            ),
            foundation_model=DEFAULT_MODEL_ID,
        )
