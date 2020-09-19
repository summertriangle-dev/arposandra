-- 
-- Migrate old t10 tracking data to new t20 table. 
-- Do not run on a live table, even though it shouldn't cause any issues.
-- 

INSERT INTO border_fixed_data_v4 (
    serverid, event_id,
    observation, is_last, tier_type,
    points_t1, userid_t1,
    points_t2, userid_t2,
    points_t3, userid_t3,
    points_t4, userid_t4,
    points_t5, userid_t5,
    points_t6, userid_t6,
    points_t7, userid_t7,
    points_t8, userid_t8,
    points_t9, userid_t9,
    points_t10, userid_t10
) 
(SELECT * from border_fixed_data_v3) 
ON CONFLICT (serverid, event_id, tier_type, observation) DO NOTHING;

UPDATE border_fixed_data_v4 SET 
    who_t1 = '???', who_t2 = '???',
    who_t3 = '???', who_t4 = '???',
    who_t5 = '???', who_t6 = '???',
    who_t7 = '???', who_t8 = '???',
    who_t9 = '???', who_t10 = '???'
WHERE observation < '2020-09-19'::timestamp