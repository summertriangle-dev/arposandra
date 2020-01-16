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

    async def _fetch_new_tier_recs(self, con, server_id, event_id):
        return await con.fetch(
            """
            WITH closest AS (
	            SELECT observation FROM border_data_v2 
	            WHERE serverid=$1 AND event_id=$2 
	            ORDER BY observation LIMIT 1
            )

            SELECT observation, CONCAT_WS('.', tier_type, tier_to) AS dataset, points
            FROM border_data_v2 WHERE serverid=$1 AND event_id=$2
            AND observation > (SELECT observation FROM closest) - INTERVAL '1 day'
            ORDER BY observation
            """, server_id, event_id
        )
    
    async def _fetch_tiers_with_afterts(self, con, server_id, event_id, ts):
        return await con.fetch(
            """
            SELECT observation, CONCAT_WS('.', tier_type, tier_to) AS dataset,
                points
            FROM border_data_v2 WHERE serverid=$1 AND event_id=$2 AND observation > $3
            ORDER BY observation
            """,
            server_id,
            event_id,
            ts
        )

    async def get_tier_records(self, server_id, event_id, after_dt):
        datasets = defaultdict(lambda: [])
        async with self.coordinator.pool.acquire() as c:
            if after_dt is not None:
                recs = await self._fetch_tiers_with_afterts(c, server_id, event_id, after_dt)
            else:
                recs = await self._fetch_new_tier_recs(c, server_id, event_id)

            for x in range(100):
                for record in recs:
                    datasets[record["dataset"]].append(
                        ((record["observation"] + timedelta(minutes=15 * x)).isoformat(), 
                        record["points"] + 101 * x)
                    )

        return datasets
    
    async def _fetch_new_t10_recs(self, con, server_id, event_id):
        return await con.fetch(
            """
            WITH closest AS (
	            SELECT observation FROM border_fixed_data_v2 
	            WHERE serverid=$1 AND event_id=$2 
	            ORDER BY observation LIMIT 1
            )

            SELECT observation, tier_type AS dataset, 
                points_t1, points_t2, points_t3, points_t4, points_t5,
                points_t6, points_t7, points_t8, points_t9, points_t10
            FROM border_fixed_data_v2 WHERE serverid=$1 AND event_id=$2
            AND observation > (SELECT observation FROM closest) - INTERVAL '1 day'
            ORDER BY observation
            """, server_id, event_id
        )
    
    async def _fetch_t10_afterts(self, con, server_id, event_id, ts):
        return await con.fetch(
            """
            SELECT observation, tier_type AS dataset, 
                points_t1, points_t2, points_t3, points_t4, points_t5,
                points_t6, points_t7, points_t8, points_t9, points_t10
            FROM border_fixed_data_v2 WHERE serverid=$1 AND event_id=$2 AND observation > $3
            ORDER BY observation
            """,
            server_id,
            event_id,
            ts
        )

    async def get_t10_records(self, server_id, event_id, after_dt):
        datasets = defaultdict(lambda: [])
        async with self.coordinator.pool.acquire() as c:
            if after_dt is not None:
                recs = await self._fetch_t10_afterts(c, server_id, event_id, after_dt)
            else:
                recs = await self._fetch_new_t10_recs(c, server_id, event_id)

            for x in range(100):
                for record in recs:
                    for x in range(1, 11):
                        datasets[f"{record['dataset']}.t{x}"].append((
                            record["observation"].isoformat(), record[f"points_t{x}"]
                        ))

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


@route(r"/api/private/saint/([a-z]+)/([0-9]+)/tiers.json")
class APISaintData(RequestHandler):
    MAX_LOOK_BACK_TIME = 86400

    async def get_data_validated(self, sid, eid, after_dt):
        return await self.settings["event_tracking"].get_tier_records(sid, eid, after_dt)

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

            if after_dt > now:
                self.set_status(400)
                self.write({"error": "Date too far in the future."})
                return

            # We only return up to 24 hours of past results. If you need
            # more, you should use CSV dumps.            
            if (now - after_dt).total_seconds() > self.MAX_LOOK_BACK_TIME:
                after_dt = None
                is_new = True
        else:
            after_dt = None
            is_new = True

        out = await self.get_data_validated(sid, int(eid), after_dt)
        self.write({"result": {"is_new": is_new, "datasets": out}})

@route(r"/api/private/saint/([a-z]+)/([0-9]+)/top10.json")
class APISaintFixedData(APISaintData):
    async def get_data_validated(self, sid, eid, after_dt):
        return await self.settings["event_tracking"].get_t10_records(sid, eid, after_dt)
