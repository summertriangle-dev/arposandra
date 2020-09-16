-- RUN THIS SCRIPT after mtrack -X to create set records for initial cards.
-- It shouldn't cause any issues if you run this multiple times.

-----------------------------------------------------
-- STEP 1: SET RELEASE DATES ON INITIAL CARDS
-----------------------------------------------------

-- muse initial urs
insert into card_index_v1__release_dates values (100013001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100023001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100033001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100043001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100053001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100063001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100073001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100083001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100093001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;

insert into card_index_v1__release_dates values (100013001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100023001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100033001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100043001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100053001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100063001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100073001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100083001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100093001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;

-- muse initial srs
insert into card_index_v1__release_dates values (100012001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100022001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100032001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100042001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100052001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100062001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100072001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100082001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100092001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;

insert into card_index_v1__release_dates values (100012001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100022001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100032001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100042001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100052001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100062001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100072001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100082001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100092001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;

-- aqours initial urs
insert into card_index_v1__release_dates values (101013001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101023001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101033001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101043001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101053001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101063001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101073001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101083001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101093001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;

insert into card_index_v1__release_dates values (101013001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101023001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101033001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101043001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101053001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101063001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101073001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101083001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101093001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;

-- aqours initial srs
insert into card_index_v1__release_dates values (101012001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101022001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101032001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101042001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101052001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101062001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101072001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101082001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101092001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;

insert into card_index_v1__release_dates values (101012001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101022001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101032001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101042001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101052001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101062001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101072001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101082001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101092001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;

-- niji initial srs
insert into card_index_v1__release_dates values (102012001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102022001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102032001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102042001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102052001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102062001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102072001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102082001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102092001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102102001, 'jp', '2020-08-08 06:00:00'::timestamp) on conflict (id, server_id) do nothing;

insert into card_index_v1__release_dates values (102012001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102022001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102032001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102042001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102052001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102062001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102072001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102082001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102092001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;

-- Lesson Time Nijigaku (SIF thanksgiving promos), ada9785d1e73894c
insert into card_index_v1__release_dates values (502011001, 'jp', '2020-04-05 03:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (502021001, 'jp', '2020-04-05 03:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (502031001, 'jp', '2020-04-05 03:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (502041001, 'jp', '2020-04-05 03:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (502051001, 'jp', '2020-04-05 03:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (502061001, 'jp', '2020-04-05 03:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (502071001, 'jp', '2020-04-05 03:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (502081001, 'jp', '2020-04-05 03:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (502091001, 'jp', '2020-04-05 03:00:00'::timestamp) on conflict (id, server_id) do nothing;

insert into card_index_v1__release_dates values (502011001, 'en', '2020-09-08 03:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (502021001, 'en', '2020-09-08 03:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (502031001, 'en', '2020-09-08 03:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (502041001, 'en', '2020-09-08 03:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (502051001, 'en', '2020-09-08 03:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (502061001, 'en', '2020-09-08 03:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (502071001, 'en', '2020-09-08 03:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (502081001, 'en', '2020-09-08 03:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (502091001, 'en', '2020-09-08 03:00:00'::timestamp) on conflict (id, server_id) do nothing;

-- INITIAL RARE SETS

-- MUSE
insert into card_index_v1__release_dates values (100011001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100021001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100031001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100041001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100051001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100061001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100071001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100081001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100091001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;

insert into card_index_v1__release_dates values (100011002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100021002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100031002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100041002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100051002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100061002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100071002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100081002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100091002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;

-- AQOURS
insert into card_index_v1__release_dates values (101011001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101021001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101031001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101041001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101051001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101061001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101071001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101081001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101091001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;

insert into card_index_v1__release_dates values (101011002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101021002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101031002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101041002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101051002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101061002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101071002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101081002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101091002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;

-- NIJI
insert into card_index_v1__release_dates values (102011001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102021001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102031001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102041001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102051001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102061001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102071001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102081001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102091001, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102101001, 'jp', '2020-08-05 06:00:00'::timestamp) on conflict (id, server_id) do nothing;

insert into card_index_v1__release_dates values (102011002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102021002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102031002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102041002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102051002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102061002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102071002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102081002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102091002, 'jp', '2019-09-26 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102101002, 'jp', '2020-08-05 06:00:00'::timestamp) on conflict (id, server_id) do nothing;

-- MUSE
insert into card_index_v1__release_dates values (100011001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100021001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100031001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100041001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100051001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100061001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100071001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100081001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100091001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;

insert into card_index_v1__release_dates values (100011002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100021002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100031002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100041002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100051002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100061002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100071002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100081002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (100091002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;

-- AQOURS
insert into card_index_v1__release_dates values (101011001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101021001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101031001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101041001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101051001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101061001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101071001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101081001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101091001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;

insert into card_index_v1__release_dates values (101011002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101021002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101031002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101041002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101051002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101061002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101071002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101081002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (101091002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;

-- NIJI
insert into card_index_v1__release_dates values (102011001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102021001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102031001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102041001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102051001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102061001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102071001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102081001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102091001, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;

insert into card_index_v1__release_dates values (102011002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102021002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102031002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102041002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102051002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102061002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102071002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102081002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;
insert into card_index_v1__release_dates values (102091002, 'en', '2020-02-24 15:00:00'::timestamp) on conflict (id, server_id) do nothing;


-----------------------------------------------------
-- STEP 2: CREATE MISSING INITIAL SETS
-----------------------------------------------------

insert into card_p_set_index_v1 values ('muse-initial-ur', 'synthetic.initial.g1.r3.ord0', 1, 0) on conflict (representative) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r3.ord0', 100013001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r3.ord0', 100023001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r3.ord0', 100033001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r3.ord0', 100043001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r3.ord0', 100053001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r3.ord0', 100063001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r3.ord0', 100073001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r3.ord0', 100083001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r3.ord0', 100093001) on conflict (representative, card_ids) do nothing;

insert into card_p_set_index_v1 values ('aqours-initial-ur', 'synthetic.initial.g2.r3.ord0', 1, 0) on conflict (representative) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r3.ord0', 101013001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r3.ord0', 101023001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r3.ord0', 101033001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r3.ord0', 101043001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r3.ord0', 101053001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r3.ord0', 101063001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r3.ord0', 101073001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r3.ord0', 101083001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r3.ord0', 101093001) on conflict (representative, card_ids) do nothing;

-- Initial SR sets already exist.

insert into card_p_set_index_v1 values ('niji-tokimeki-runners', 'synthetic.initial.g3.r2.ord0', 1, 1) on conflict (representative) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r2.ord0', 102012001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r2.ord0', 102022001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r2.ord0', 102032001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r2.ord0', 102042001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r2.ord0', 102052001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r2.ord0', 102062001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r2.ord0', 102072001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r2.ord0', 102082001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r2.ord0', 102092001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r2.ord0', 102102001) on conflict (representative, card_ids) do nothing;

insert into card_p_set_index_v1 values ('muse-initial-r-uniform', 'synthetic.initial.g1.r1.ord0', 1, 0) on conflict (representative) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r1.ord0', 100011001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r1.ord0', 100021001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r1.ord0', 100031001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r1.ord0', 100041001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r1.ord0', 100051001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r1.ord0', 100061001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r1.ord0', 100071001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r1.ord0', 100081001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r1.ord0', 100091001) on conflict (representative, card_ids) do nothing;

insert into card_p_set_index_v1 values ('aqours-initial-r-uniform', 'synthetic.initial.g2.r1.ord0', 1, 0) on conflict (representative) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r1.ord0', 101011001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r1.ord0', 101021001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r1.ord0', 101031001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r1.ord0', 101041001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r1.ord0', 101051001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r1.ord0', 101061001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r1.ord0', 101071001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r1.ord0', 101081001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r1.ord0', 101091001) on conflict (representative, card_ids) do nothing;

insert into card_p_set_index_v1 values ('niji-initial-r-uniform', 'synthetic.initial.g3.r1.ord0', 1, 1) on conflict (representative) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r1.ord0', 102011001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r1.ord0', 102021001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r1.ord0', 102031001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r1.ord0', 102041001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r1.ord0', 102051001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r1.ord0', 102061001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r1.ord0', 102071001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r1.ord0', 102081001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r1.ord0', 102091001) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r1.ord0', 102101001) on conflict (representative, card_ids) do nothing;

insert into card_p_set_index_v1 values ('muse-initial-r-prologue', 'synthetic.initial.g1.r1.ord1', 1, 0) on conflict (representative) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r1.ord1', 100011002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r1.ord1', 100021002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r1.ord1', 100031002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r1.ord1', 100041002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r1.ord1', 100051002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r1.ord1', 100061002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r1.ord1', 100071002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r1.ord1', 100081002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g1.r1.ord1', 100091002) on conflict (representative, card_ids) do nothing;

insert into card_p_set_index_v1 values ('aqours-initial-r-prologue', 'synthetic.initial.g2.r1.ord1', 1, 0) on conflict (representative) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r1.ord1', 101011002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r1.ord1', 101021002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r1.ord1', 101031002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r1.ord1', 101041002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r1.ord1', 101051002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r1.ord1', 101061002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r1.ord1', 101071002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r1.ord1', 101081002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g2.r1.ord1', 101091002) on conflict (representative, card_ids) do nothing;

insert into card_p_set_index_v1 values ('niji-initial-r-prologue', 'synthetic.initial.g3.r1.ord1', 1, 1) on conflict (representative) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r1.ord1', 102011002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r1.ord1', 102021002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r1.ord1', 102031002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r1.ord1', 102041002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r1.ord1', 102051002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r1.ord1', 102061002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r1.ord1', 102071002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r1.ord1', 102081002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r1.ord1', 102091002) on conflict (representative, card_ids) do nothing;
insert into card_p_set_index_v1__card_ids values ('synthetic.initial.g3.r1.ord1', 102101002) on conflict (representative, card_ids) do nothing;


-----------------------------------------------------
-- STEP 3: UPDATE SORT DATES
-----------------------------------------------------
-- COPYPASTED FROM mtrack scripts.py
-- Niji initial sets will order higher than normal due to Shioriko's initials being added
-- in August.

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