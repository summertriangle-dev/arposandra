from datetime import datetime, timedelta
from collections import defaultdict

from tornado.web import RequestHandler

from .dispatch import route
from . import pageutils


class EventTrackingDatabase(object):
    SERVER_IDS = ["jp"]

    def __init__(self, coordinator):
        self.coordinator = coordinator

    def validate_server_id(self, server_id):
        if server_id not in self.SERVER_IDS:
            return self.SERVER_IDS[0]
        return server_id

    async def get_event_info(self, server_id, event_id):
        async with self.coordinator.pool.acquire() as c:
            return await c.fetchrow(
                """
                SELECT event_id, banner, event_type, start_t, end_t, result_t FROM event_v2
                WHERE serverid=$1 AND event_id=$2
                """,
                server_id,
                event_id,
            )

    async def get_current_event(self, server_id, timestamp):
        async with self.coordinator.pool.acquire() as c:
            return await c.fetchrow(
                """
                SELECT event_id, banner, event_type, start_t, end_t, result_t FROM event_v2
                WHERE serverid=$1 AND start_t <= $2 AND result_t < $2 ORDER BY end_t DESC
                """,
                server_id,
                timestamp,
            )

    async def get_stories(self, server_id, event_id):
        async with self.coordinator.pool.acquire() as c:
            return await c.fetch(
                """
                SELECT chapter, req_points, banner, title, script_path FROM event_story_v2
                WHERE serverid=$1 AND event_id=$2 ORDER BY chapter
                """,
                server_id,
                event_id,
            )

    async def get_tier_records(self, server_id, event_id, after_dt):
        datasets = defaultdict(lambda: [])
        async with self.coordinator.pool.acquire() as c:
            recs = await c.fetch(
                """
                SELECT observation, CONCAT_WS('.', tier_type, tier_to) AS dataset,
                    points
                FROM border_data_v2 WHERE serverid=$1 AND event_id=$2 AND observation > $3
                ORDER BY observation
                """,
                server_id,
                event_id,
                after_dt,
            )

            for y in range(50):
                for record in recs:
                    datasets[record["dataset"]].append(
                        (record["observation"].isoformat(), record["points"])
                    )

        return datasets


@route(r"/events")
@route(r"/events/([0-9]+)(?:/[^/]*)")
class EventServerRedirect(RequestHandler):
    def get(self, eid=None):
        target = self.get_cookie("dsid", "jp")
        # TODO: centralize list of servers
        target = self.settings["event_tracking"].validate_server_id(target)

        if eid:
            self.redirect(f"/{target}/events/{eid}")
        else:
            self.redirect(f"/{target}/events")


@route(r"/([a-z]+)/events")
@route(r"/([a-z]+)/events/([0-9]+)(?:/[^/]*)?")
class EventDash(RequestHandler):
    async def get(self, sid, eid=None):
        sid = self.settings["event_tracking"].validate_server_id(sid)

        if not eid:
            current = datetime.utcnow()
            event = await self.settings["event_tracking"].get_current_event(sid, current)
        else:
            event = await self.settings["event_tracking"].get_event_info(sid, int(eid))
            if not event:
                self.set_status(404)
                return "I don't remember an event with this ID."

        stories_list = await self.settings["event_tracking"].get_stories(sid, event["event_id"])
        self.render("event_scaffold.html", server_id=sid, event_rec=event, stories=stories_list)


@route(r"/api/private/saint/([a-z]+)/current/setup.json")
@route(r"/api/private/saint/([a-z]+)/([0-9]+)/setup.json")
class APISaintInfo(RequestHandler):
    async def get(self, sid, eid=None):
        if self.settings["event_tracking"].validate_server_id(sid) != sid:
            self.set_status(400)
            self.write({"error": "This is not a valid server ID."})

        if not eid:
            current = datetime.utcnow()
            event = await self.settings["event_tracking"].get_current_event(sid, current)
        else:
            event = await self.settings["event_tracking"].get_event_info(sid, int(eid))
            if not event:
                self.set_status(404)
                self.write({"error": "No such event ID."})

        self.write(
            {
                "result": {
                    "event_id": event["event_id"],
                    "start_time": event["start_t"].isoformat(),
                    "end_time": event["end_t"].isoformat(),
                    "result_time": event["result_t"].isoformat(),
                    "title_image": pageutils.image_url_reify(self, event["banner"], "png"),
                }
            }
        )


@route(r"/api/private/saint/([a-z]+)/([0-9]+)/data.json")
class APISaintData(RequestHandler):
    MAX_LOOK_BACK_TIME = 86400

    async def get(self, sid, eid=None):
        if self.settings["event_tracking"].validate_server_id(sid) != sid:
            self.set_status(400)
            self.write({"error": "This is not a valid server ID."})

        is_new = False
        now = datetime.utcnow()

        after_ts = self.get_argument("after", None)
        if after_ts:
            try:
                after_dt = datetime.utcfromtimestamp(int(after_ts))
            except ValueError:
                self.set_status(400)
                self.write({"error": "Invalid timestamp given for after parameter."})
                return
        else:
            after_dt = now - timedelta(seconds=self.MAX_LOOK_BACK_TIME)
            is_new = True

        if after_dt > now:
            self.set_status(400)
            self.write({"error": "Date too far in the future."})
            return

        # We only return up to 24 hours of past results. If you need
        # more, you should use CSV dumps.
        if (now - after_dt).total_seconds() > self.MAX_LOOK_BACK_TIME:
            after_dt = now - timedelta(seconds=self.MAX_LOOK_BACK_TIME)
            is_new = True

        out = await self.settings["event_tracking"].get_tier_records(sid, int(eid), after_dt)
        self.write({"result": {"is_new": is_new, "datasets": out}})

