import sys
import json
import asyncio
from unittest import mock
from datetime import datetime
import logging
import time

import astool
import iceapi
import models


def begin_session_2(tag, cfg):
    with open("border/tests/fetchBootstrap.json", "r") as ff:
        bs_t, _1, _2, m_bootstrap, _3 = json.load(ff)
    with open("border/tests/fetchEventMining.json", "r") as ff:
        met_t, _1, _2, m_event_top, _3 = json.load(ff)
    with open("border/tests/fetchEventMiningRanking.json", "r") as ff:
        mer_t, _1, _2, m_event_ranking, _3 = json.load(ff)
    # with open("border/tests/fetchEventMarathon.json", "r") as ff:
    #    m_event_top_marathon = json.load(ff)[3]
    with open("border/tests/fetchEventMarathonRanking.json", "r") as ff:
        merm_t, _1, _2, m_event_ranking_marathon, _3 = json.load(ff)

    session = mock.Mock()
    session.device_token = "abcd"
    session.api.bootstrap.fetchBootstrap.return_value = iceapi.api_return_t(
        {}, 0, m_bootstrap, bs_t / 1000
    )
    session.api.eventMining.fetchEventMining.return_value = iceapi.api_return_t(
        {}, 0, m_event_top, met_t / 1000
    )
    session.api.eventMiningRanking.fetchEventMiningRanking.return_value = iceapi.api_return_t(
        {}, 0, m_event_ranking, mer_t / 1000
    )
    # session.api.eventMarathon.fetchEventMarathon.return_value = iceapi.api_return_t({}, 0, m_event_top_marathon)
    session.api.eventMarathonRanking.fetchEventMarathonRanking.return_value = iceapi.api_return_t(
        {}, 0, m_event_ranking_marathon, merm_t / 1000
    )
    return session


def end_session_2(tag, ice):
    pass


def begin_session(tag, cfg) -> iceapi.ICEBinder:
    with astool.astool_memo(tag) as memo:
        uid = memo.get("user_id")
        pwd = memo.get("password")
        auc = memo.get("auth_count")
        fast_resume = memo.get("resume_data")

    if not all((uid, pwd)):
        raise ValueError("You need an account to do that.")

    ice = iceapi.ICEBinder(cfg, "iOS", uid, pwd, auc)
    if not ice.resume_session(fast_resume):
        ret = ice.api.login.login()
        if ret.return_code != 0:
            logging.info("Login failed, trying to reset auth count...")
            ice.set_login(uid, pwd, ret.app_data.get("authorization_count") + 1)
            ice.api.login.login()

    return ice


def end_session(tag, ice: iceapi.ICEBinder):
    with astool.astool_memo(tag) as memo:
        memo["master_version"] = ice.master_version
        memo["auth_count"] = ice.auth_count
        memo["resume_data"] = ice.save_session()


#####################################################################

EMPTY_IMAGE = {"v": None}
EMPTY_TEXT = {"dot_under_text": None}


async def write_common_event_status(
    db: models.DatabaseConnection, region: str, event_main_struct: dict, event_type: str
):
    stories = []
    if "story_status" in event_main_struct:
        for story in event_main_struct["story_status"].get("stories", []):
            stories.append(
                (
                    region,
                    event_main_struct["event_id"],
                    story["story_number"],
                    story.get("required_event_point", 0),
                    story.get("story_banner_thumbnail_path", EMPTY_IMAGE)["v"],
                    story.get("title", EMPTY_TEXT)["dot_under_text"],
                    story.get("scenario_script_asset_path", EMPTY_IMAGE)["v"],
                )
            )

    await db.add_event(
        region,
        event_main_struct["event_id"],
        None,
        event_main_struct["title_image_path"]["v"],
        event_type,
        event_main_struct["start_at"],
        event_main_struct["expired_at"],
        event_main_struct["result_at"],
        stories,
    )


TWO_MINUTES = 120
HALF_DAY = 43200
FULL_DAY = 86400
TRACK_INTERVAL_NOW = 1
TRACK_INTERVAL_ACCELERATED = 900
TRACK_INTERVAL = 3600


def track_interval(current: datetime, status: models.event_status_t):
    if current < status.start_time:
        return False

    since_start = current - status.start_time
    to_end = status.end_time - current

    if to_end.total_seconds() < TWO_MINUTES:
        logging.info("Event is ending - tracking immediately")
        return True

    if since_start.total_seconds() < HALF_DAY or to_end.total_seconds() < FULL_DAY:
        logging.info("On accelerated track pace")
        if current.minute in [13, 14, 15, 28, 29, 30, 43, 44, 45, 58, 59, 0]:
            return True

    if current.minute in [58, 59, 0]:
        return True


def should_track_for_event(status: models.event_status_t):
    current = datetime.utcnow()

    if status.have_final:
        logging.info("Not collecting data because event has ended with final results.")
        return False

    if current > status.end_time and current < status.results_time:
        logging.info(
            "Not collecting data because event has ended and final results are unavailable."
        )
        return False

    if status.last_collect_time is not None:
        since_last = current - status.last_collect_time
        if not track_interval(current, status):
            logging.info("Not collecting data because it's not time.")
            return False

    return True


def make_common_top100_rows(cell_coll, userinfo_key):
    return [
        (
            cell["order"],
            cell["event_point"],
            cell[userinfo_key]["user_id"],
            cell[userinfo_key]["user_name"]["dot_under_text"],
            cell[userinfo_key]["user_rank"],
            cell[userinfo_key]["card_master_id"],
            cell[userinfo_key]["level"],
            cell[userinfo_key]["is_awakening"],
            cell[userinfo_key]["is_all_training_activated"],
            cell[userinfo_key]["emblem_master_id"],
        )
        for cell in cell_coll
    ]


def make_common_top10_row(cell_coll, rank_type, userinfo_key):
    l = [rank_type]
    max_ = len(cell_coll)
    for x in range(10):
        if x >= max_:
            l.append(None)
            l.append(None)
            continue

        l.append(cell_coll[x]["event_point"])
        l.append(cell_coll[x][userinfo_key]["user_id"])
    return l


def make_common_border_rows(row_coll, rank_type):
    for tier in row_coll:
        if tier["ranking_border_master_row"]["ranking_type"] != 1:
            continue
        if not tier["ranking_border_master_row"].get("lower_rank"):
            continue

        yield (
            rank_type,
            tier["ranking_border_point"],
            tier["ranking_border_master_row"]["upper_rank"],
            tier["ranking_border_master_row"]["lower_rank"],
        )


async def fetch_marathon_event_border(
    ice: iceapi.ICEBinder, region: str, db: models.DatabaseConnection, eid: int
):
    is_new_event = False

    if not await db.have_event_info(region, eid):
        logging.info("Need to fetch event description for %s %d", region, eid)
        event_info = ice.api.eventMarathon.fetchEventMarathon({"event_id": eid,}).app_data

        main = event_info["event_marathon_top_status"]
        await write_common_event_status(db, region, main, "marathon")
        is_new_event = True

    status = await db.get_event_status(region, eid)
    if (not is_new_event) and (not should_track_for_event(status)):
        return

    ranking_info = ice.api.eventMarathonRanking.fetchEventMarathonRanking(
        {"event_id": eid,}
    ).app_data
    observe_time = datetime.utcnow()

    if observe_time > status.results_time:
        logging.info("Getting final word...")
        is_last = True
    else:
        is_last = False

    fixed_rows = []
    flex_rows = []

    top_pt_ranking = ranking_info.get("top_ranking_cells")
    if top_pt_ranking:
        top_pt_ranking = sorted(top_pt_ranking, key=lambda x: x["order"])
        fixed_rows.append(
            make_common_top10_row(top_pt_ranking, "points", "event_marathon_ranking_user")
        )
        flex_rows.append(
            ("points", top_pt_ranking[-1]["event_point"], 0, top_pt_ranking[-1]["order"])
        )

    pt_ranking = ranking_info.get("ranking_border_info")
    if pt_ranking:
        flex_rows.extend(make_common_border_rows(pt_ranking, "points"))

    logging.info("Adding %d entries", len(flex_rows))
    await db.add_tiers(region, eid, observe_time, is_last, flex_rows, fixed_rows)

    if is_last and top_pt_ranking:
        await db.add_t100(
            region,
            eid,
            "points",
            make_common_top100_rows(top_pt_ranking, "event_marathon_ranking_user"),
        )


async def fetch_mining_event_border(
    ice: iceapi.ICEBinder, region: str, db: models.DatabaseConnection, eid: int
):
    is_new_event = False
    if not await db.have_event_info(region, eid):
        logging.info("Need to fetch event description for %s %d", region, eid)
        event_info = ice.api.eventMining.fetchEventMining({"event_id": eid,}).app_data

        main = event_info["event_mining_top_status"]
        await write_common_event_status(db, region, main, "mining")
        is_new_event = True

    status = await db.get_event_status(region, eid)
    if (not is_new_event) and (not should_track_for_event(status)):
        return

    iced = ice.api.eventMiningRanking.fetchEventMiningRanking({"event_id": eid,})
    ranking_info = iced.app_data
    observe_time = datetime.utcfromtimestamp(iced.server_time)

    if observe_time > status.results_time:
        logging.info("Getting final word...")
        is_last = True
    else:
        is_last = False

    fixed_rows = []
    flex_rows = []

    top_pt_ranking = ranking_info.get("point_top_ranking_cells")
    if top_pt_ranking:
        top_pt_ranking = sorted(top_pt_ranking, key=lambda x: x["order"])
        fixed_rows.append(
            make_common_top10_row(top_pt_ranking, "points", "event_mining_ranking_user")
        )
        flex_rows.append(
            ("points", top_pt_ranking[-1]["event_point"], 0, top_pt_ranking[-1]["order"])
        )

    top_score_ranking = ranking_info.get("voltage_top_ranking_cells")
    if top_score_ranking:
        top_score_ranking = sorted(top_score_ranking, key=lambda x: x["order"])
        fixed_rows.append(
            make_common_top10_row(top_score_ranking, "voltage", "event_mining_ranking_user")
        )
        flex_rows.append(
            ("voltage", top_score_ranking[-1]["event_point"], 0, top_score_ranking[-1]["order"])
        )

    pt_ranking = ranking_info.get("point_ranking_border_info")
    if pt_ranking:
        flex_rows.extend(make_common_border_rows(pt_ranking, "points"))

    score_ranking = ranking_info.get("voltage_ranking_border_info")
    if score_ranking:
        flex_rows.extend(make_common_border_rows(score_ranking, "voltage"))

    logging.info("Adding %d entries", len(flex_rows))
    await db.add_tiers(region, eid, observe_time, is_last, flex_rows, fixed_rows)

    if is_last:
        if top_pt_ranking:
            await db.add_t100(
                region,
                eid,
                "points",
                make_common_top100_rows(top_pt_ranking, "event_mining_ranking_user"),
            )
        if top_score_ranking:
            await db.add_t100(
                region,
                eid,
                "voltage",
                make_common_top100_rows(top_score_ranking, "event_mining_ranking_user"),
            )


async def get_event_border(ice, region, db):
    status = ice.api.bootstrap.fetchBootstrap(
        {
            "bootstrap_fetch_types": [2, 3, 4, 5, 9, 10],
            "device_token": ice.device_token,
            "device_name": "iPhoneX",
        }
    ).app_data

    event = status.get("fetch_bootstrap_pickup_info_response", {}).get("active_event")
    if not event:
        logging.info("No event.")
        return

    eid = event["event_id"]

    if event["event_type"] == 2:
        await fetch_mining_event_border(ice, region, db, eid)
    elif event["event_type"] == 1:
        await fetch_marathon_event_border(ice, region, db, eid)


async def main():
    logging.basicConfig(level=logging.INFO)
    tag = sys.argv[1]
    cfg = astool.resolve_server_config(astool.SERVER_CONFIG[tag])

    ice = begin_session(tag, cfg)
    try:
        db = models.DatabaseConnection()
        await db.init_models()
        await get_event_border(ice, tag, db)
    finally:
        end_session(tag, ice)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
