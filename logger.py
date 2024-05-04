import logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)-8s] %(message)s (%(filename)s:%(lineno)s)",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)
