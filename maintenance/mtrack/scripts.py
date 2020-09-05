# TODO: I haven't looked very carefully at optimizing these queries.
# May want to come back after a couple years and see how they're doing.

# Updates the set event reference list (list of history records that feature cards
# in the set) based on newly added entries.
def update_set_event_refs(prefix):
    return f"""
        INSERT INTO card_p_set_index_v1__event_references
            (SELECT representative, serverid, {prefix}history_v5.id FROM {prefix}history_v5
                INNER JOIN {prefix}history_v5__card_ids USING (id, serverid) 
                INNER JOIN card_p_set_index_v1__card_ids USING (card_ids)
                INNER JOIN card_p_set_index_v1 USING (representative))
            ON CONFLICT (representative, server_id, record_id) DO NOTHING
    """


# Tries to set the release date based on feature list from newly added history
# records. If a card was released without a feature and featured later, the
# date will be set wrong. This won't happen though. In theory...
def update_card_release_dates(prefix):
    return f"""
        WITH rdates AS (
            SELECT DISTINCT ON (card_ids) 
                card_ids, {prefix}history_v5.what, {prefix}history_v5.start_time 
            FROM {prefix}history_v5__card_ids 
            INNER JOIN card_index_v1 ON (card_ids = card_index_v1.id 
                AND card_index_v1.release_date IS NULL) 
            INNER JOIN {prefix}history_v5 ON (
                {prefix}history_v5__card_ids.id = {prefix}history_v5.id 
                AND {prefix}history_v5__card_ids.serverid = {prefix}history_v5.serverid
            )
            ORDER BY card_ids, start_time
        )

        UPDATE card_index_v1 SET 
            (release_date, source) = (SELECT start_time, what FROM rdates WHERE card_ids = id)
    """


# Tries to set the release date based on feature list from newly added history
# records. If a card was released without a feature and featured later, the
# date will be set wrong. This won't happen though. In theory...
def update_set_per_server_release_dates(prefix):
    return f"""
        WITH hts AS (
            SELECT representative, server_id, id, start_time FROM {prefix}history_v5
            INNER JOIN card_p_set_index_v1__event_references ON (
                id = record_id AND {prefix}history_v5.serverid = card_p_set_index_v1__event_references.server_id
            )
        )
        
        INSERT INTO card_p_set_index_v1__release_dates (
            SELECT representative, server_id, MIN(start_time), MAX(start_time) 
            FROM hts GROUP BY (representative, server_id)
        ) ON CONFLICT (representative, server_id) DO UPDATE SET
            min_date = LEAST(card_p_set_index_v1__release_dates.min_date, excluded.min_date),
            max_date = GREATEST(card_p_set_index_v1__release_dates.max_date, excluded.max_date)
    """


def update_set_per_server_release_dates_synthetic():
    return """
        INSERT INTO card_p_set_index_v1__event_references
        (SELECT representative, serverid, history_v5__card_ids.id FROM card_p_set_index_v1
            INNER JOIN card_p_set_index_v1__card_ids USING (representative)
            INNER JOIN history_v5__card_ids USING (card_ids) 
            WHERE representative LIKE 'synthetic.%'
        )
        ON CONFLICT (representative, server_id, record_id) DO NOTHING;
        
        WITH hts AS (
            SELECT representative, server_id, id, start_time FROM card_p_set_index_v1__event_references
            INNER JOIN history_v5 ON (
                id = record_id AND history_v5.serverid = card_p_set_index_v1__event_references.server_id
            )
            WHERE representative LIKE 'synthetic.%'
        )
        
        INSERT INTO card_p_set_index_v1__release_dates (
            SELECT representative, server_id, MIN(start_time), MAX(start_time) 
            FROM hts GROUP BY (representative, server_id)
        ) ON CONFLICT (representative, server_id) DO UPDATE SET
            min_date = LEAST(card_p_set_index_v1__release_dates.min_date, excluded.min_date),
            max_date = GREATEST(card_p_set_index_v1__release_dates.max_date, excluded.max_date)
    """


# Sets set_type to EVENT for set records where needed (we assume that event sets have
# at most one event and one gacha record associated).
# NOTE: hardcodes jp as serverid, since it is the most recent
def update_event_sets():
    return f"""
        WITH min_rd AS (SELECT DISTINCT * FROM (
            SELECT DISTINCT ON (card_ids) representative AS pk, history_v5.id, what 
            FROM card_p_set_index_v1__card_ids 
            INNER JOIN history_v5__card_ids USING (card_ids)
            INNER JOIN history_v5 USING (id, serverid)
            WHERE history_v5__card_ids.serverid = 'jp'
	        ORDER BY card_ids, start_time
        ) AS sub1), assoc_count AS (
            SELECT pk, what FROM min_rd GROUP BY (pk, what) HAVING COUNT(0) = 1
        )

	
        -- WITH assoc_count AS (
        --     SELECT card_p_set_index_v1.id, representative AS pk, what FROM card_p_set_index_v1 
        --     INNER JOIN card_p_set_index_v1__event_references USING (representative)
        --     INNER JOIN history_v5 ON (record_id = history_v5.id AND serverid = server_id)
        --     WHERE server_id = 'jp'
        --     GROUP BY (representative, what) HAVING COUNT(0) = 1
        -- )

        UPDATE card_p_set_index_v1 SET set_type = 2
        -- don't want to clobber song/ordinal/etc sets
        WHERE card_p_set_index_v1.set_type = 1 
            AND representative IN (SELECT pk FROM assoc_count WHERE what = 2 AND pk = representative) 
    """
