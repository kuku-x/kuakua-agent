from kuakua_agent.api.app import create_app
from kuakua_agent.services.scheduler import PraiseScheduler
from kuakua_agent.services.activitywatch import ActivityWatchScheduler

app = create_app()

scheduler: PraiseScheduler | None = None
aw_scheduler: ActivityWatchScheduler | None = None


@app.on_event("startup")
async def startup():
    global scheduler, aw_scheduler
    scheduler = PraiseScheduler()
    await scheduler.start()
    aw_scheduler = ActivityWatchScheduler()
    await aw_scheduler.start()


@app.on_event("shutdown")
async def shutdown():
    if scheduler:
        await scheduler.stop()
    if aw_scheduler:
        await aw_scheduler.stop()
