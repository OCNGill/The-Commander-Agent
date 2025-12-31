#!/usr/bin/env python3
"""
Minimal HTPC agent — sends a heartbeat to the relay and logs locally.
Replace with your agent logic (task execution, model calls, etc.).
"""
import os
import time
import logging
import urllib.request
import urllib.parse

HERE = os.path.dirname(__file__)
LOG_DIR = os.environ.get('AGENT_LOG_DIR') or os.path.join(os.path.abspath(os.path.join(HERE, '..')), 'logs', 'agents')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'htpc_agent.log')

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', filename=LOG_FILE)
logger = logging.getLogger('htpc_agent')

RELAY_URL = os.environ.get('RELAY_URL', 'http://127.0.0.1:8002/heartbeat')

def send_heartbeat():
    data = urllib.parse.urlencode({'agent': 'htpc', 'status': 'alive'}).encode()
    req = urllib.request.Request(RELAY_URL, data=data, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            logger.info('Heartbeat sent, response: %s', resp.read().decode('utf-8', errors='replace'))
    except Exception as e:
        logger.exception('Failed to send heartbeat: %s', e)

if __name__ == '__main__':
    logger.info('HTPC agent starting')
    try:
        while True:
            send_heartbeat()
            time.sleep(int(os.environ.get('HEARTBEAT_INTERVAL', '10')))
    except KeyboardInterrupt:
        logger.info('HTPC agent stopping')
