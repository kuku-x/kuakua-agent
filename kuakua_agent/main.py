from kuakua_agent.api.app import create_app
from kuakua_agent.services.storage_layer import get_database
from kuakua_agent.services.monitor.scheduler import PraiseScheduler
from kuakua_agent.services.monitor.activitywatch import ActivityWatchScheduler
from kuakua_agent.services.monitor.nightly_summary_scheduler import NightlySummaryScheduler

app = create_app()

scheduler: PraiseScheduler | None = None
aw_scheduler: ActivityWatchScheduler | None = None
nightly_summary_scheduler: NightlySummaryScheduler | None = None


@app.on_event("startup")
async def startup():
    global scheduler, aw_scheduler, nightly_summary_scheduler
    db = get_database()
    await db.init_db()
    scheduler = PraiseScheduler()
    await scheduler.start()
    aw_scheduler = ActivityWatchScheduler()
    await aw_scheduler.start()
    nightly_summary_scheduler = NightlySummaryScheduler()
    await nightly_summary_scheduler.start()


@app.on_event("shutdown")
async def shutdown():
    if scheduler:
        await scheduler.stop()
    if aw_scheduler:
        await aw_scheduler.stop()
    if nightly_summary_scheduler:
        await nightly_summary_scheduler.stop()
