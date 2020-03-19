import copy
import heapq
import logging
from datetime import datetime, timedelta

from celery import schedules
from celery.beat import ScheduleEntry, Scheduler, event_t
from django.utils import timezone
from django_geosource.models import PostGISSource

logger = logging.getLogger(__name__)


class SourceEntry(ScheduleEntry):
    def __init__(self, source, *args, **kwargs):
        self.source = source
        self.name = source.slug
        super().__init__(*args, **kwargs)

    def is_due(self):
        logger.info(f"Is {self.source} due to refresh ?")

        if self.source.refresh > 0:
            next_run = self.last_run_at + timedelta(minutes=self.source.refresh)
            logger.debug(
                f"Refresh : {self.source.refresh} | Next run : {next_run} | Now : {timezone.now()}"
            )
            if next_run < timezone.now():
                logger.info("Source is due to refresh")
                return schedules.schedstate(True, 10.0)
            else:
                logger.debug("Source is NOT due to refresh, let's wait")
                return schedules.schedstate(False, 10.0)

        logger.info("The refresh is disabled for this source, check again later")
        return schedules.schedstate(False, 600.0)

    def run_task(self):
        logger.info(f"Launch refresh_data for source {self.source}")
        try:
            self.source.run_async_method("refresh_data")
        except Exception as e:
            logger.error(f"Refresh data couldn't be launched: {e}")

    def __next__(self, last_run_at=None):
        """Return new instance, with date and count fields updated."""
        return self.__class__(
            **dict(
                self,
                source=self.source,
                last_run_at=last_run_at or self.default_now(),
                total_run_count=self.total_run_count + 1,
            )
        )

    next = __next__


class GeosourceScheduler(Scheduler):
    """Database-backed Beat Scheduler."""

    Entry = SourceEntry
    _initial = True
    _last_sync = None

    TICK_DELAY = 60

    def all_entries(self):
        s = {}
        for source in PostGISSource.objects.exclude(refresh__lte=0).order_by(
            "-refresh"
        ):
            try:
                s[source.slug] = self.Entry(source, app=self.app)
            except ValueError:
                pass
        return s

    def reserve(self, entry):
        new_entry = self.schedule[entry.source.slug] = next(entry)
        return new_entry

    @property
    def schedule(self):
        if self.should_sync():
            logger.debug("Resync schedule entries")
            self.sync()
            self._schedule = self.all_entries()

        return self._schedule

    def sync(self):
        self._last_sync = timezone.now().timestamp()
        super().sync()

    def should_sync(self):
        last_update = PostGISSource.objects.order_by("-updated_at").first()
        if not self._last_sync or (
            last_update
            and (
                timezone.make_aware(
                    datetime.fromtimestamp(self._last_sync),
                    timezone.get_default_timezone(),
                )
                < last_update.updated_at
            )
        ):
            return True
        return False

    def apply_entry(self, entry, producer=None):
        logger.info(f"Scheduler: Sending due task {entry.source.name}")
        entry.run_task()

    def tick(
        self, event_t=event_t, min=min, heappop=heapq.heappop, heappush=heapq.heappush
    ):

        logger.debug("Ticking")

        max_interval = self.max_interval

        if self._heap is None or not self.schedules_equal(
            self.old_schedulers, self.schedule
        ):
            self.old_schedulers = copy.copy(self.schedule)
            self.populate_heap()

        H = self._heap

        if not H:
            logger.info("There is no source to synchronize")
            return max_interval

        event = H[0]
        time_to_run, priority, entry = event
        time_to_run = datetime.fromtimestamp(time_to_run)

        if time_to_run < datetime.now():
            is_due, next_time_to_run = self.is_due(entry)
            verify = heappop(H)

            if is_due and verify is event:
                self.apply_entry(entry, producer=self.producer)

            next_entry = self.reserve(entry)
            heappush(
                H,
                event_t(self._when(next_entry, next_time_to_run), priority, next_entry),
            )

        return self.TICK_DELAY / len(H)
