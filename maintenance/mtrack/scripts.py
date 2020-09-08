# TODO: I haven't looked very carefully at optimizing these queries.
# May want to come back after a couple years and see how they're doing.

# We sort based on latest release.
def update_set_sort_table():
    return f"""
        INSERT INTO card_p_set_index_v1__sort_dates
            (SELECT representative, server_id, MAX(date) FROM card_index_v1__release_dates
                INNER JOIN card_p_set_index_v1__card_ids ON (id = card_ids)
                GROUP BY (representative, server_id))
            ON CONFLICT (representative, server_id) DO UPDATE SET
                date = excluded.date;

        WITH rd AS (
            SELECT representative, (CASE WHEN MIN(date) < '2020-08-05 08:00:00'::timestamp THEN 0 ELSE 1 END) AS have_shio
                FROM card_index_v1__release_dates
                INNER JOIN card_p_set_index_v1__card_ids ON (id = card_ids)
                WHERE server_id = 'jp'
                GROUP BY (representative)
        )
        UPDATE card_p_set_index_v1 SET shioriko_exists = 
            (SELECT have_shio FROM rd WHERE rd.representative = card_p_set_index_v1.representative)
        WHERE shioriko_exists IS NULL;

        -- Do it twice for sets without a release date.
        UPDATE card_p_set_index_v1 SET shioriko_exists = 0
        WHERE shioriko_exists IS NULL 
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
                AND what = type
            )
            ORDER BY card_id, {prefix}history_v5__dates.serverid, date
        )

        INSERT INTO card_index_v1__release_dates (
            (SELECT card_id, serverid, date FROM rdates)
        ) ON CONFLICT DO NOTHING;

        UPDATE card_index_v1 SET 
            source = (SELECT what FROM {prefix}history_v5__card_ids WHERE card_id = card_index_v1.id LIMIT 1)
    """
