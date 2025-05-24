from diagrams import Diagram, Cluster
from diagrams.onprem.client import User
from diagrams.aws.network import APIGateway
from diagrams.aws.compute import ECS
from diagrams.onprem.network import Internet
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB

with Diagram("eWhiteboard System Workflow", show=False, direction="LR"):
    user = User("User")
    internet = Internet("Browser")
    with Cluster("Docker Host"):
        elb = ELB("Nginx Proxy")
        with Cluster("App Layer"):
            api = APIGateway("Django API")
            ecs = ECS("Django App")
        db = RDS("Amazon RDS\n(PostgreSQL)")
    user >> internet >> elb >> api >> ecs >> db
    db >> ecs >> elb >> internet >> user
