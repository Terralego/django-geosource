import logging
from datetime import timedelta
import traceback
from django.utils import timezone

from celery.beat import Scheduler, ScheduleEntry
from django_geosource.models import PostGISSource

logger = logging.getLogger(__name__)


class SourceEntry(ScheduleEntry):
    def __init__(self, source, *args, **kwargs):
        self.source = source
        super().__init__(*args, **kwargs)

    def is_due(self):
        if self.source.refresh > 0:
            logger.info(f'Refresh : {self.source.refresh}')
            next_run = self.last_run_at + timedelta(seconds=self.source.refresh)
            if next_run >= timezone.now():
                logger.info(self.source.refresh)
                return True, self.source.refresh * 10
            logger.info(self.last_run_at)

        return False, 600

    def run_task(self):
        logger.info(f'Launch refresh_data for source {self.source}')
        self.source.run_async_method('refresh_data', force=True)

class GeosourceScheduler(Scheduler):
    """Database-backed Beat Scheduler."""

    Entry = SourceEntry
    # Changes = PeriodicTasks

    def __init__(self, *args, **kwargs):
        Scheduler.__init__(self, *args, **kwargs)

    def all_entries(self):
        s = {}
        for source in PostGISSource.objects.all().order_by('-refresh')[:2]:
            try:
                s[source.slug] = self.Entry(source, app=self.app)
            except ValueError:
                pass
        return s

    @property
    def schedule(self):
        # initial = update = False
        # if self._initial_read:
        #     logger.debug('DatabaseScheduler: initial read')
        #     initial = update = True
        #     self._initial_read = False
        # elif self.schedule_changed():
        #     logger.info('DatabaseScheduler: Schedule changed.')
        #     update = True
        update = True
        initial = True
        if update:
            self.sync()

            self._schedule = self.all_entries()

            # the schedule changed, invalidate the heap in Scheduler.tick
            if not initial:
                self._heap = []
                self._heap_invalidated = True
        return self._schedule

    def apply_entry(self, entry, producer=None):
        logger.info(f'Scheduler: Sending due task {entry.source.name}')
        try:
            entry.run_task()
        except Exception as exc:
            logger.error('Message Error: %s\n%s', exc, traceback.format_stack(), exc_info=True)
