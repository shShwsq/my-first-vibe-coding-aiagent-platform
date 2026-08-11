import logging
import sys


def setup_logging():
    """统一配置日志格式和级别"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    
    logging.getLogger('app.routers.unified_agent_chat').setLevel(logging.DEBUG)
