-- news/ingest.py
CREATE TABLE IF NOT EXISTS news_v2 (
    serverid varchar(8),
    news_id int,
    thumbnail varchar(16),
    title text,
    ts timestamp,
    internal_category int,
    body_html text,
    body_dm text,
    card_refs text,
    visible bool,
    PRIMARY KEY (serverid, news_id)
);
-- mtrack
CREATE TABLE IF NOT EXISTS card_tracking_v1 (
    serverid varchar(8),
    card_id int,
    card_ordinal int,
    firstseen_master varchar(32),
    probably_type int,
    norm_date date,
    PRIMARY KEY (serverid, card_id)
);

-- Saint
DO $$ BEGIN
    CREATE TYPE tier_type_t AS ENUM ('points', 'voltage');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS event_v2 (
    serverid varchar(8),
    event_id int,
    event_title text,
    banner text,
    event_type text,
    start_t timestamp,
    end_t timestamp,
    result_t timestamp,

    UNIQUE(serverid, event_id)
);
CREATE TABLE IF NOT EXISTS event_story_v2 (
    serverid varchar(8),
    event_id int,
    chapter int,
    req_points int,
    banner text,
    title text,
    script_path text,

    FOREIGN KEY (serverid, event_id) REFERENCES event_v2(serverid, event_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS border_fixed_data_v3 (
    serverid varchar(8),
    event_id int,
    observation timestamp,
    is_last boolean,

    tier_type tier_type_t,
    points_t1 int, userid_t1 int,
    points_t2 int, userid_t2 int,
    points_t3 int, userid_t3 int,
    points_t4 int, userid_t4 int,
    points_t5 int, userid_t5 int,
    points_t6 int, userid_t6 int,
    points_t7 int, userid_t7 int,
    points_t8 int, userid_t8 int,
    points_t9 int, userid_t9 int,
    points_t10 int, userid_t10 int,

    UNIQUE (serverid, event_id, tier_type, observation),
    FOREIGN KEY (serverid, event_id) REFERENCES event_v2(serverid, event_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS border_data_v3 (
    serverid varchar(8),
    event_id int,
    observation timestamp,
    is_last boolean,

    tier_type tier_type_t,
    points int,
    tier_from int,
    tier_to int,

    UNIQUE(serverid, event_id, tier_type, tier_to, observation),
    FOREIGN KEY (serverid, event_id) REFERENCES event_v2(serverid, event_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- tlinject_model.py
CREATE TABLE IF NOT EXISTS tlinject_v1 (
    langid varchar(8),
    key text,
    translated text,
    sender varchar(48),
    ts timestamp
);
CREATE TABLE IF NOT EXISTS tlinject_cache_v1 (
    langid varchar(8),
    key text,
    translated text,
    PRIMARY KEY (langid, key)
);
CREATE TABLE IF NOT EXISTS tlinject_languages_v1 (
    langid varchar(8) primary key
);

INSERT INTO tlinject_languages_v1 VALUES ('en') ON CONFLICT DO NOTHING;
