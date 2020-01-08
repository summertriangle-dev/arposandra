from collections import OrderedDict
from datetime import date
from dataclasses import dataclass


@dataclass
class CardTrackingByDate(object):
    date: date
    card_refs: list
    master: str
    server: str


class CardTrackingDatabase(object):
    def __init__(self, coordinator):
        self.coordinator = coordinator

    async def get_history_entries(self, for_server, before_time, limit):
        async with self.coordinator.pool.acquire() as c:
            items = await c.fetch(
                """SELECT card_id, firstseen_master, probably_type, norm_date
                    FROM card_tracking_v1 WHERE norm_date < $1 ORDER BY norm_date DESC""",
                before_time,
            )

        g = OrderedDict()
        for row in items:
            if row["norm_date"] not in g:
                g[row["norm_date"]] = CardTrackingByDate(
                    row["norm_date"], [], row["firstseen_master"], for_server
                )
            g[row["norm_date"]].card_refs.append(row["card_id"])

        return list(g.values())

