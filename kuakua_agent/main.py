from kuakua_agent.api.app import create_app
from kuakua_agent.services.scheduler import PraiseScheduler

app = create_app()

scheduler: PraiseScheduler | None = None


@app.on_event("startup")
async def startup():
    global scheduler
    scheduler = PraiseScheduler()
    await scheduler.start()


@app.on_event("shutdown")
async def shutdown():
    if scheduler:
        await scheduler.stop()
