from datetime import datetime, timedelta

from tornado.web import RequestHandler

from .dispatch import route, LanguageCookieMixin, DatabaseMixin
from . import pageutils


@route(r"/events/?")
@route(r"/events/([0-9]+)(?:/[^/]*)")
class EventServerRedirect(DatabaseMixin, RequestHandler):
    def get(self, eid=None):
        target = self.get_cookie("dsid", "jp")
        # TODO: centralize list of servers
        target = self.database().event_tracker.validate_server_id(target)

        if eid:
            self.redirect(f"/{target}/events/{eid}")
        else:
            self.redirect(f"/{target}/events")


@route(r"/([a-z]+)/(events|events_high)/?")
@route(r"/([a-z]+)/(events|events_high)/([0-9]+)(?:/[^/]*)?")
class EventDash(DatabaseMixin, LanguageCookieMixin):
    def to_track_mode(self, urltype):
        if urltype == "events_high":
            return "top10"
        return "normal"

    async def get(self, sid, ttype, eid=None):
        sid = self.database().event_tracker.validate_server_id(sid)

        if not eid:
            current = datetime.utcnow()
            event = await self.database().event_tracker.get_current_event(sid, current)
        else:
            event = await self.database().event_tracker.get_event_info(sid, int(eid))

        if not event:
            self.set_status(404)
            self.render("error.html", message="There's no event with this ID.")
            return

        self.resolve_cards(event)
        stories_list = await self.database().event_tracker.get_stories(sid, event.id)
        self.render(
            "event_scaffold.html",
            server_id=sid,
            event_rec=event,
            stories=stories_list,
            track_mode=self.to_track_mode(ttype),
        )

    def resolve_cards(self, item):
        cards = self.settings["master"].lookup_multiple_cards_by_id(item.feature_card_ids)
        item.feature_card_ids = [c for c in cards if c]


@route(r"/api/private/saint/([a-z]+)/current/setup.json")
@route(r"/api/private/saint/([a-z]+)/([0-9]+)/setup.json")
class APISaintInfo(DatabaseMixin):
    async def get(self, sid, eid=None):
        if self.database().event_tracker.validate_server_id(sid) != sid:
            self.set_status(400)
            self.write({"error": "This is not a valid server ID."})

        if not eid:
            current = datetime.utcnow()
            event = await self.database().event_tracker.get_current_event(sid, current)
        else:
            event = await self.database().event_tracker.get_event_info(sid, int(eid))
            if not event:
                self.set_status(404)
                self.write({"error": "No such event ID."})

        self.write(
            {
                "result": {
                    "event_id": event.id,
                    "start_time": event.start_t.isoformat(),
                    "end_time": event.end_t.isoformat(),
                    "result_time": event.result_t.isoformat(),
                    "title_image": pageutils.image_url_reify(
                        self, event.thumbnail, "jpg", region=sid
                    ),
                }
            }
        )


@route(r"/api/private/saint/([a-z]+)/([0-9]+)/tiers.json")
class APISaintData(DatabaseMixin):
    MAX_LOOK_BACK_TIME = 86400

    async def get_data_validated(self, sid, eid, after_dt):
        return await self.database().event_tracker.get_tier_records(sid, eid, after_dt)

    async def get(self, sid, eid=None):
        if self.database().event_tracker.validate_server_id(sid) != sid:
            self.set_status(400)
            self.write({"error": "This is not a valid server ID."})

        is_new = False
        now = datetime.utcnow()

        after_ts = self.get_argument("after", None)
        tscale_hrs = self.get_argument("back", "24")
        try:
            tscale_hrs = int(tscale_hrs)
            if tscale_hrs < 1:
                tscale_hrs = 24
        except ValueError:
            tscale_hrs = 24

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
                tscale_hrs = 24
                after_dt = None
                is_new = True
        else:
            after_dt = None
            is_new = True

        if is_new:
            out = await self.get_data_validated(sid, int(eid), tscale_hrs)
        else:
            out = await self.get_data_validated(sid, int(eid), after_dt)

        if is_new:
            self.set_header(
                "Expires", (now + timedelta(minutes=15)).strftime("%a, %d %b %Y %H:%M:%S GMT")
            )

        self.write({"result": {"is_new": is_new, "datasets": out}})


@route(r"/api/private/saint/([a-z]+)/([0-9]+)/top10.json")
class APISaintFixedData(APISaintData):
    async def get_data_validated(self, sid, eid, after_dt):
        return await self.database().event_tracker.get_t10_records(sid, eid, after_dt)
