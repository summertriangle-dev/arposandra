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
        m_bootstrap = json.load(ff)[3]
    with open("border/tests/fetchEventMining.json", "r") as ff:
        m_event_top = json.load(ff)[3]
    with open("border/tests/fetchEventMiningRanking.json", "r") as ff:
        m_event_ranking = json.load(ff)[3]
    #with open("border/tests/fetchEventMarathon.json", "r") as ff:
    #    m_event_top_marathon = json.load(ff)[3]
    with open("border/tests/fetchEventMarathonRanking.json", "r") as ff:
        m_event_ranking_marathon = json.load(ff)[3]

    session = mock.Mock()
    session.device_token = "abcd"
    session.api.bootstrap.fetchBootstrap.return_value = iceapi.api_return_t({}, 0, m_bootstrap)
    session.api.eventMining.fetchEventMining.return_value = iceapi.api_return_t({}, 0, m_event_top)
    session.api.eventMiningRanking.fetchEventMiningRanking.return_value = iceapi.api_return_t({}, 0, m_event_ranking)
    #session.api.eventMarathon.fetchEventMarathon.return_value = iceapi.api_return_t({}, 0, m_event_top_marathon)
    session.api.eventMarathonRanking.fetchEventMarathonRanking.return_value = iceapi.api_return_t({}, 0, m_event_ranking_marathon)
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
            print("Login failed, trying to reset auth count...")
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

async def fetch_marathon_event_border(ice, 
    region: str,
    db: models.DatabaseConnection, 
    eid: int):
    if not await db.have_event_info(region, eid):
        logging.info("Need to fetch event description for %s %d", region, eid)
        event_info = ice.api.eventMarathon.fetchEventMarathon({
            "event_id": eid,
        }).app_data

        main = event_info["event_marathon_top_status"]

        stories = []
        if "story_status" in main:
            for story in main["story_status"].get("stories", []):
                stories.append((
                    main["event_id"],
                    story["story_number"],
                    story.get("required_event_point", 0),
                    story.get("story_banner_thumbnail_path", EMPTY_IMAGE)["v"],
                    story.get("title", EMPTY_TEXT)["dot_under_text"],
                    story.get("scenario_script_asset_path", EMPTY_IMAGE)["v"]
                ))

        await db.add_event(
            region,
            main["event_id"], 
            None,
            main["title_image_path"]["v"],
            "marathon",
            main["start_at"], 
            main["expired_at"],
            main["result_at"],
            stories
        )
    
    d = datetime.utcnow()
    endt, resultst = await db.get_event_timing(region, eid)
    if d > endt and d < resultst:
        logging.info("Event ended, not collecting data.")
        return

    if await db.have_final_tiers(region, eid):
        return

    ranking_info = ice.api.eventMarathonRanking.fetchEventMarathonRanking({
        "event_id": eid,
    }).app_data
    observe_time = datetime.utcnow()

    if observe_time > resultst:
        logging.info("Getting final word...")
        is_last = True
    else:
        is_last = False

    send_to_db = []
    pt_ranking = ranking_info.get("ranking_border_info")
    if pt_ranking:
        for tier in pt_ranking:
            if tier["ranking_border_master_row"]["ranking_type"] != 1:
                continue
            if not tier["ranking_border_master_row"].get("lower_rank"):
                continue
        
            send_to_db.append((
                "points",
                tier["ranking_border_point"],
                tier["ranking_border_master_row"]["upper_rank"],
                tier["ranking_border_master_row"]["lower_rank"],
                tier["ranking_border_master_row"]["display_order"],
            ))
    
    logging.info("Adding %d entries", len(send_to_db))
    await db.add_tiers(region, eid, observe_time, is_last, send_to_db)

async def fetch_mining_event_border(ice, 
    region: str,
    db: models.DatabaseConnection, 
    eid: int):
    if not await db.have_event_info(region, eid):
        logging.info("Need to fetch event description for %s %d", region, eid)
        event_info = ice.api.eventMining.fetchEventMining({
            "event_id": eid,
        }).app_data

        main = event_info["event_mining_top_status"]

        stories = []
        if "story_status" in main:
            for story in main["story_status"].get("stories", []):
                stories.append((
                    region,
                    main["event_id"],
                    story["story_number"],
                    story.get("required_event_point", 0),
                    story.get("story_banner_thumbnail_path", EMPTY_IMAGE)["v"],
                    story.get("title", EMPTY_TEXT)["dot_under_text"],
                    story.get("scenario_script_asset_path", EMPTY_IMAGE)["v"]
                ))

        await db.add_event(
            region,
            main["event_id"], 
            None,
            main["title_image_path"]["v"],
            "mining",
            main["start_at"], 
            main["expired_at"],
            main["result_at"],
            stories
        )
    
    d = datetime.utcnow()
    endt, resultst = await db.get_event_timing(region, eid)
    if d > endt and d < resultst:
        logging.info("Event ended, not collecting data.")
        return

    if await db.have_final_tiers(region, eid):
        return

    ranking_info = ice.api.eventMiningRanking.fetchEventMiningRanking({
        "event_id": eid,
    }).app_data
    observe_time = datetime.utcnow()

    if observe_time > resultst:
        logging.info("Getting final word...")
        is_last = True
    else:
        is_last = False

    send_to_db = []
    pt_ranking = ranking_info.get("point_ranking_border_info")
    if pt_ranking:
        for tier in pt_ranking:
            if tier["ranking_border_master_row"]["ranking_type"] != 1:
                continue
            if not tier["ranking_border_master_row"].get("lower_rank"):
                continue
        
            send_to_db.append((
                "points",
                tier["ranking_border_point"],
                tier["ranking_border_master_row"]["upper_rank"],
                tier["ranking_border_master_row"]["lower_rank"],
                tier["ranking_border_master_row"]["display_order"],
            ))
    
    score_ranking = ranking_info.get("voltage_ranking_border_info")
    if score_ranking:
        for tier in score_ranking:
            if tier["ranking_border_master_row"]["ranking_type"] != 1:
                continue
            if not tier["ranking_border_master_row"].get("lower_rank"):
                continue
        
            send_to_db.append((
                "voltage",
                tier["ranking_border_point"],
                tier["ranking_border_master_row"]["upper_rank"],
                tier["ranking_border_master_row"]["lower_rank"],
                tier["ranking_border_master_row"]["display_order"],
            ))
    
    logging.info("Adding %d entries", len(send_to_db))
    await db.add_tiers(region, eid, observe_time, is_last, send_to_db)


async def get_event_border(ice, region, db, tag):
    status = ice.api.bootstrap.fetchBootstrap({
        "bootstrap_fetch_types": [2, 3, 4, 5, 9, 10],
        "device_token": ice.device_token,
        "device_name": "iPhoneX"
    }).app_data

    event = status["fetch_bootstrap_pickup_info_response"].get("active_event")
    if not event:
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
        await get_event_border(ice, tag, db, tag)
    finally:
        end_session(tag, ice)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
