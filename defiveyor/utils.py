import asyncio
import datetime
import logging
import random
import sys
from typing import Optional


def configure_logging():
    log_format = "[%(asctime)s.%(msecs)03d] [%(process)d] [%(threadName)s] [%(levelname)s] %(name)s: %(message)s"
    log_date_format = "%Y-%m-%d %H:%M:%S"
    message_format = logging.Formatter(fmt=log_format, datefmt=log_date_format)
    logging.root.setLevel(logging.DEBUG)

    # setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(fmt=message_format)
    logging.root.addHandler(console_handler)


class ContinuousRateLimiter:
    def __init__(
        self,
        operations_per_second: float,
        jitter_seconds: Optional[float] = None,
        name: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.max_operations_per_second = float(operations_per_second)
        self.jitter_seconds = (
            float(jitter_seconds) if jitter_seconds is not None else None
        )
        self.last_operation_time: Optional[datetime.datetime] = None
        self.sleep_per_operation_seconds: float = 1.0 / self.max_operations_per_second
        self.name = name
        self.logger = logger or logging.getLogger("rate_limiter")

    async def next(self, ops: int = 1):
        time_to_next_op_seconds: float
        if self.last_operation_time:
            time_since_last_operation: datetime.timedelta = (
                datetime.datetime.utcnow() - self.last_operation_time
            )
            time_to_next_op_seconds = (
                self.sleep_per_operation_seconds
                - time_since_last_operation.total_seconds()
            )
            if self.jitter_seconds is not None:
                time_to_next_op_seconds += random.random() * self.jitter_seconds
        else:
            time_to_next_op_seconds = 0.0

        if time_to_next_op_seconds > 0:
            self.logger.debug(
                f"[{self.name or 'generic'}] "
                f"waiting {time_to_next_op_seconds:0.03}s before next operation"
                f" (rate={self.max_operations_per_second:0.03}/s)"
            )
            await asyncio.sleep(time_to_next_op_seconds)

        self.last_operation_time = datetime.datetime.utcnow()

    def apply(self):
        def _wrap_rate_limited(func):
            async def _rate_limited(*args, **kwargs):
                await self.next()
                return await func(*args, **kwargs)

            return _rate_limited

        return _wrap_rate_limited

    @staticmethod
    def make(
        name: str,
        *,
        operations_per_hour: Optional[float] = None,
        operations_per_minute: Optional[float] = None,
        operations_per_second: Optional[float] = None,
        jitter_percentage: Optional[float] = None,
        logger: Optional[logging.Logger] = None,
    ):
        operations_per_second = operations_per_second or 0
        if operations_per_minute is not None:
            operations_per_second += operations_per_minute / 60
        if operations_per_hour is not None:
            operations_per_second += operations_per_hour / (60 * 60)
        if operations_per_second == 0:
            raise ValueError("rate limiter cannot be unlimited")

        if jitter_percentage is not None:
            jitter_seconds = jitter_percentage / operations_per_second
        else:
            jitter_seconds = None

        return ContinuousRateLimiter(
            name=name,
            operations_per_second=operations_per_second,
            jitter_seconds=jitter_seconds,
            logger=logger,
        )
