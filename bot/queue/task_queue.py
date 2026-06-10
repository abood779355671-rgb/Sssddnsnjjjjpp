import asyncio
import logging
from typing import Callable, Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)


@dataclass
class Task:
    task_id: str
    user_id: int
    coro_fn: Callable
    args: tuple
    kwargs: dict
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    retries: int = 0
    max_retries: int = 3


class DownloadQueue:
    """Async task queue with concurrency control and retry."""

    def __init__(self, max_concurrent: int = 5, max_retries: int = 3):
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self._queue: asyncio.Queue = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active_tasks: Dict[str, Task] = {}
        self._user_active: Dict[int, int] = {}
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None

    async def start(self):
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
        logger.info(f"Download queue started (max_concurrent={self.max_concurrent})")

    async def stop(self):
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    async def add_task(self, user_id: int, coro_fn: Callable, *args, **kwargs) -> str:
        task_id = str(uuid.uuid4())[:8]
        task = Task(
            task_id=task_id,
            user_id=user_id,
            coro_fn=coro_fn,
            args=args,
            kwargs=kwargs,
            max_retries=self.max_retries,
        )
        await self._queue.put(task)
        logger.debug(f"Task {task_id} queued for user {user_id}")
        return task_id

    async def _worker(self):
        while self._running:
            try:
                task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                asyncio.create_task(self._execute_task(task))
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue worker error: {e}")

    async def _execute_task(self, task: Task):
        async with self._semaphore:
            self._active_tasks[task.task_id] = task
            self._user_active[task.user_id] = self._user_active.get(task.user_id, 0) + 1
            try:
                await task.coro_fn(*task.args, **task.kwargs)
            except Exception as e:
                logger.error(f"Task {task.task_id} failed (attempt {task.retries+1}): {e}")
                if task.retries < task.max_retries:
                    task.retries += 1
                    await asyncio.sleep(2 ** task.retries)
                    await self._queue.put(task)
            finally:
                self._active_tasks.pop(task.task_id, None)
                if task.user_id in self._user_active:
                    self._user_active[task.user_id] -= 1
                    if self._user_active[task.user_id] <= 0:
                        del self._user_active[task.user_id]

    def get_active_count(self) -> int:
        return len(self._active_tasks)

    def get_queue_size(self) -> int:
        return self._queue.qsize()

    def is_user_active(self, user_id: int) -> bool:
        return self._user_active.get(user_id, 0) > 0


# Global queue instance
download_queue = DownloadQueue(max_concurrent=5)
