import sys
import json
import asyncio
from unittest import mock
from datetime import datetime
import logging

import astool
import iceapi
import ingest
import dm_parse

def begin_session_2(tag, cfg):
    with open("news/test/fetchNotice.json", "r") as mock_n_list:
        m_notices = json.load(mock_n_list)
    with open("news/test/fetchNoticeDetail.json", "r") as mock_n_body:
        m_single = json.load(mock_n_body)[3]

    session = mock.Mock()
    session.api.notice.fetchNotice.return_value = iceapi.api_return_t({}, 0, m_notices)
    session.api.notice.fetchNoticeDetail.return_value = iceapi.api_return_t({}, 0, m_single)
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

def get_notice_body(ice, nid: int):
    ret = ice.api.notice.fetchNoticeDetail({
        "notice_id": nid
    })
    return ret.app_data["notice"].get("detail_text", {}).get("dot_under_text", "")

def pairwise(iterable):
    a = iter(iterable)
    return zip(a, a)

async def add_notice(ice, db, tag, notice):
    thumb = notice.get("banner_thumbnail", {}).get("v")
    title = notice.get("title", {}).get("dot_under_text", "")
    ts = datetime.utcfromtimestamp(notice["date"])
    nid = notice["notice_id"]
    cat = notice["category"]

    body_dm = get_notice_body(ice, nid)
    body_html, c_refs, _ = dm_parse.dm_to_html(body_dm.encode("utf8"))

    print("Adding notice:", nid)
    await db.insert_notice(tag, nid, title, ts, cat, thumb, body_dm, body_html, c_refs)

async def get_new_notices(ice, db, tag):
    since = await db.get_epoch(tag)
    ret = ice.api.notice.fetchNotice().app_data
    vis_set = set()
    seen = set()
    for _, the_list in pairwise(ret["notice_lists"]):
        for no in the_list["notices"]:
            vis_set.add(no["notice_id"])
            if datetime.utcfromtimestamp(no["date"]) <= since:
                continue
            if no["notice_id"] in seen:
                continue
            await add_notice(ice, db, tag, no)
            seen.add(no["notice_id"])
    
    await db.update_visibility(list(vis_set))

async def main():
    logging.basicConfig(level=logging.INFO)
    tag = sys.argv[1]
    cfg = astool.resolve_server_config(astool.SERVER_CONFIG[tag])

    ice = begin_session(tag, cfg)
    try:
        db = ingest.DatabaseConnection()
        await get_new_notices(ice, db, tag)
    finally:
        end_session(tag, ice)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
