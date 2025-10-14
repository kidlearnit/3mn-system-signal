#!/usr/bin/env python3
"""
Base classes and utilities for RQ workers (OOP-style)
"""

import os
import logging
import redis
from rq import Worker, Queue, Connection
from logging_config import configure_logging


class BaseRQWorker:
    """
    Base class encapsulating common RQ worker setup and lifecycle.
    Subclasses should override get_listen_queues() to specify queues.
    """

    def __init__(self, redis_url: str | None = None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://redis:6379/0')
        self._conn = redis.from_url(self.redis_url)

    def get_listen_queues(self) -> list[str]:
        """Return list of queue names to listen to."""
        raise NotImplementedError

    def run(self, with_scheduler: bool = True):
        """Start the RQ worker loop."""
        configure_logging()
        listen = self.get_listen_queues()
        self.logger.info("Starting RQ worker", extra={"queues": listen})
        with Connection(self._conn):
            worker = Worker(map(Queue, listen))
            worker.work(with_scheduler=with_scheduler)


