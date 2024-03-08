import logging

logging.basicConfig(
    level=logging.INFO,
    format="{'time':'%(asctime)s', 'level': '%(levelname)s', 'message': '%(message)s'}",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)