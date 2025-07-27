#!/usr/bin/env python3
"""
Gunicorn configuration for production deployment
"""

import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
backlog = 2048

# Worker processes
workers = int(os.environ.get('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2 + 1))
worker_class = os.environ.get('WORKER_CLASS', 'gevent')
worker_connections = int(os.environ.get('WORKER_CONNECTIONS', '1000'))
threads = int(os.environ.get('WORKER_THREADS', '2'))
keepalive = 2

# Worker recycling
max_requests = int(os.environ.get('MAX_REQUESTS', '1000'))
max_requests_jitter = int(os.environ.get('MAX_REQUESTS_JITTER', '50'))

# Timeout configuration
timeout = 30
graceful_timeout = 30

# Logging
accesslog = '-'
errorlog = '-'
loglevel = os.environ.get('LOG_LEVEL', 'info').lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'prp-gunicorn'

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# SSL/TLS (if terminating at application level)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

# StatsD integration (optional)
# statsd_host = 'localhost:8125'
# statsd_prefix = 'prp'

def pre_fork(server, worker):
    """Called just before a worker is forked"""
    server.log.info("Worker spawning (pid: %s)", worker.pid)

def pre_exec(server):
    """Called just before a new master process is forked"""
    server.log.info("Forking new master process")

def when_ready(server):
    """Called just after the server is started"""
    server.log.info("Server is ready. Listening at: %s", server.address)

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT"""
    worker.log.info("Worker received INT or QUIT signal")

def post_fork(server, worker):
    """Called just after a worker has been forked"""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal"""
    worker.log.info("Worker received SIGABRT signal")