# TODO: I haven't looked very carefully at optimizing these queries.
# May want to come back after a couple years and see how they're doing.

# We sort based on latest release.
def update_set_sort_table():
    return f"""
        INSERT INTO card_p_set_index_v2__sort_dates
            (SELECT representative, server_id, MAX(date) FROM card_index_v1__release_dates
                INNER JOIN card_p_set_index_v2__card_ids ON (id = card_ids)
                GROUP BY (representative, server_id))
            ON CONFLICT (representative, server_id) DO UPDATE SET
                date = excluded.date;

        WITH rd AS (
            SELECT representative, (CASE WHEN MIN(date) < '2020-08-05 08:00:00'::timestamp THEN 0 ELSE 1 END) AS have_shio
                FROM card_index_v1__release_dates
                INNER JOIN card_p_set_index_v2__card_ids ON (id = card_ids)
                WHERE server_id = 'jp'
                GROUP BY (representative)
        )
        UPDATE card_p_set_index_v2 SET nijigasaki_member_state = 
            (SELECT have_shio FROM rd WHERE rd.representative = card_p_set_index_v2.representative)
        WHERE nijigasaki_member_state IS NULL;

        -- Do it twice for sets without a release date.
        UPDATE card_p_set_index_v2 SET nijigasaki_member_state = 0
        WHERE nijigasaki_member_state IS NULL 
    """


# Tries to set the release date based on feature list from newly added history
# records. If a card was released without a feature and featured later, the
# date will be set wrong. This won't happen though. In theory...
def update_card_release_dates(prefix):
    return f"""
        WITH rdates AS (
            SELECT DISTINCT ON (card_id, {prefix}history_v5__dates.serverid) 
                card_id, {prefix}history_v5__dates.serverid, {prefix}history_v5__dates.date 
            FROM {prefix}history_v5__card_ids 
            INNER JOIN {prefix}history_v5__dates ON (
				{prefix}history_v5__dates.id = {prefix}history_v5__card_ids.id
                AND {prefix}history_v5__card_ids.serverid = {prefix}history_v5__dates.serverid
                AND type = (CASE 
                        WHEN what = 2 THEN 1 
                        WHEN what = 3 THEN 2 
                        WHEN what = 4 THEN 2 
                        ELSE 2
                    END)
            )
            ORDER BY card_id, {prefix}history_v5__dates.serverid, date
        )

        INSERT INTO card_index_v1__release_dates (
            (SELECT card_id, serverid, date FROM rdates)
        ) ON CONFLICT DO NOTHING;

        -- First try the entire history table, because we want the oldest source, but restrict to cards that appeared in the partial update.
        UPDATE card_index_v1 SET 
            source = (SELECT history_v5__card_ids.what FROM history_v5__card_ids 
                      INNER JOIN history_v5 USING (id, serverid) WHERE card_id = card_index_v1.id 
                      ORDER BY sort_date LIMIT 1)
            WHERE (SELECT what FROM {prefix}history_v5__card_ids WHERE card_id = card_index_v1.id LIMIT 1) IS NOT NULL;
        
        -- If still null it wasn't featured before, so go ahead and use the new hist list
        UPDATE card_index_v1 SET 
            source = (SELECT what FROM {prefix}history_v5__card_ids WHERE card_id = card_index_v1.id LIMIT 1)
            WHERE source IS NULL
    """


def update_hist_event_link():
    return """
        WITH event_match AS (
            SELECT event_v2.serverid AS sid, event_id, history_v5__dates.id AS hid FROM history_v5__dates 
            INNER JOIN event_v2 ON (history_v5__dates.serverid=event_v2.serverid 
                AND EXTRACT(epoch FROM history_v5__dates.date - event_v2.start_t) = 0)
            WHERE type = 1
        )

        INSERT INTO history_v5__dates (
            (SELECT hid, sid, 7, NULL, event_id FROM event_match)
        ) ON CONFLICT DO NOTHING;
    """
