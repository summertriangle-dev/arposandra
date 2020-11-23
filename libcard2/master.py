import os
import sqlite3
from collections import OrderedDict, defaultdict
from functools import lru_cache
from typing import Iterable, Sequence

from cachetools import LFUCache

from . import dataclasses as D
from .skill_cs_enums import TT as TriggerType, CT as ConditionType
from .utils import construct_tt_from_sql_shape
from .wave_description_base import LANGUAGE_DEFINITION_JA


class MasterDataLite(object):
    def __init__(self, master_path):
        self.version = os.path.basename(master_path.rstrip("/"))
        self.connection = sqlite3.connect(
            "file:{0}?mode=ro".format(os.path.join(master_path, "masterdata.db")), uri=True
        )
        self.connection.row_factory = sqlite3.Row

    def lookup_inline_image(self, iip):
        path = self.connection.execute(
            "SELECT path FROM m_inline_image WHERE id=?", (iip,)
        ).fetchone()
        if path:
            return path[0]

        # ???
        path = self.connection.execute(
            "SELECT path FROM m_decoration_texture WHERE id=?", (iip,)
        ).fetchone()
        if path:
            return path[0]

        return None


class MasterData(MasterDataLite):
    def __init__(self, master_path):
        super().__init__(master_path)
        self.card_id_cache = LFUCache(256)
        self.member_cache = {}
        self.card_brief_cache = {}

        self.ordinal_to_cid = {
            ord: id for ord, id in self.connection.execute("SELECT school_idol_no, id FROM m_card")
        }
        self.tt_stat_increases = self.distill_tt_stat_increases()
        self.constants = self.fetch_required_constants()
        print(f"MasterData: alloc with {len(self.ordinal_to_cid)} cards")

    def distill_tt_stat_increases(self):
        rs = self.connection.execute(
            """SELECT m_card.id AS demux, training_content_type, required_grade, SUM(value)
                FROM m_card
                LEFT JOIN m_training_tree ON (m_training_tree.id = m_card.training_tree_m_id)
                LEFT JOIN m_training_tree_card_param ON
                    (m_training_tree.training_tree_card_param_m_id = m_training_tree_card_param.id)
                LEFT JOIN m_training_tree_mapping ON
                    (m_training_tree.training_tree_mapping_m_id = m_training_tree_mapping.id)
                LEFT JOIN m_training_tree_cell_content ON (
                    m_training_tree_mapping.training_tree_cell_content_m_id = m_training_tree_cell_content.id AND
                    m_training_tree_cell_content.training_content_no = m_training_tree_card_param.training_content_no AND
                    m_training_tree_cell_content.training_tree_cell_type == 2)
                GROUP BY demux, required_grade, training_content_type
                ORDER BY demux, required_grade"""
        )

        ret = defaultdict(lambda: defaultdict(lambda: {}))
        for cid, stat, grade, sum_value in rs:
            ret[cid][grade][stat] = sum_value

        return {k: self.cumulative_tt_offset(v) for k, v in ret.items()}

    def cumulative_tt_offset(self, levels):
        ls = []
        a = 0
        s = 0
        t = 0
        for k, v in sorted(levels.items()):
            a += v.get(3, 0)
            s += v.get(2, 0)
            t += v.get(4, 0)
            ls.append(D.Card.LevelValues(k, a, s, t))
        return ls

    def fetch_required_constants(self):
        result = self.connection.execute(
            "SELECT value FROM m_constant_int WHERE constant_int = 33"
        ).fetchone()

        return D.EmbeddedConstants(result[0] if result else 0.0)

    # ---- End of init-time functions -----------------------------------------

    def _register_card_brief_cache(self, briefs: Iterable[D.CardLite]):
        self.card_brief_cache.update({x.id: x for x in briefs})

    def lookup_member_by_id(self, member_id: int) -> D.Member:
        if member_id in self.member_cache:
            return self.member_cache[member_id]

        da = self.connection.execute(
            """SELECT m_member.id, member_group, m_member_unit.member_unit AS subunit, school_grade AS year,
                name, name_romaji, birth_month, birth_day, m_member.theme_dark_color,
                m_member_group.group_name, m_member_unit.unit_name,
                thumbnail_image_asset_path,
                standing_image_asset_path, autograph_image_asset_path,
                member_icon_image_asset_path FROM m_member
                LEFT JOIN m_member_group USING (member_group)
                LEFT JOIN m_member_unit_detail ON (m_member_unit_detail.member_m_id == m_member.id)
                LEFT JOIN m_member_unit ON (m_member_unit_detail.member_unit == m_member_unit.member_unit)
                WHERE m_member.id = ? LIMIT 1""",
            (member_id,),
        ).fetchone()

        if not da:
            return None

        m = D.Member(*da)

        da = self.connection.execute(
            """SELECT id, school_idol_no, card_rarity_type, card_attribute,
                role, thumbnail_asset_path
                FROM m_card
                LEFT JOIN m_card_appearance ON (card_m_id = m_card.id AND appearance_type == 1)
                WHERE member_m_id = ? ORDER BY m_card.school_idol_no""",
            (member_id,),
        )

        m.card_brief = [
            D.CardLite(*row[:5], D.Card.Appearance(None, None, row[5]), None) for row in da
        ]

        self._register_card_brief_cache(m.card_brief)
        self.member_cache[member_id] = m
        return m

    def lookup_member_list(self, group: int = None, subunit: int = None):
        if group and subunit:
            where = "WHERE member_group = :group AND m_member_unit.member_unit = :unit"
        elif group:
            where = "WHERE member_group = :group"
        elif subunit:
            where = "WHERE m_member_unit.member_unit = :unit"
        else:
            where = ""

        ids = self.connection.execute(
            f"""SELECT m_member.id FROM m_member
                LEFT JOIN m_member_unit_detail ON (m_member_unit_detail.member_m_id == m_member.id)
                LEFT JOIN m_member_unit ON (m_member_unit_detail.member_unit == m_member_unit.member_unit)
                {where}
                ORDER BY m_member.id""",
            {"unit": subunit, "group": group},
        )

        return [self.lookup_member_by_id(i) for i, in ids]

    def all_ordinals(self):
        return sorted(self.ordinal_to_cid.keys())

    def card_ordinals_to_ids(self, ordinals: Iterable[int]):
        return [self.ordinal_to_cid.get(o) for o in ordinals]

    def lookup_card_by_id(self, card_id: int, use_cache: bool = True):
        if card_id in self.card_id_cache:
            return self.card_id_cache[card_id]

        da = self.connection.execute(
            """SELECT m_card.member_m_id, m_card.id, school_idol_no, card_rarity_type, max_level,
                card_attribute, role, training_tree_m_id, sp_point, exchange_item_id, max_passive_skill_slot,
                m_card_attribute.background_asset_path, parameter2, parameter1, parameter3,
                m_suit.thumbnail_image_asset_path, m_suit.id, m_card_live_const.critical_rate_offset
                FROM m_card
                LEFT JOIN m_card_rarity USING (card_rarity_type)
                LEFT JOIN m_card_attribute USING (card_attribute)
                LEFT JOIN m_card_awaken_parameter ON (m_card_awaken_parameter.card_master_id == m_card.id)
                LEFT JOIN m_card_live_const ON (m_card_live_const.card_master_id == m_card.id)
                LEFT JOIN m_suit ON (m_suit.suit_release_value == m_card.id AND m_suit.suit_release_route = 1)
                WHERE m_card.id = ? LIMIT 1""",
            (card_id,),
        ).fetchone()

        if not da:
            return None

        normal_appearance = None
        idolized_appearance = None
        appearances = self.connection.execute(
            """SELECT appearance_type, card_name, image_asset_path, thumbnail_asset_path FROM m_card_appearance
                WHERE card_m_id = ? ORDER BY appearance_type LIMIT 2""",
            (da[1],),
        ).fetchall()

        for type_, *row in appearances:
            if type_ == 1:
                normal_appearance = D.Card.Appearance(*row)
            if type_ == 2:
                idolized_appearance = D.Card.Appearance(*row)

        card = D.Card(
            da[1],
            da[2],
            da[3],
            da[4],
            da[5],
            da[6],
            da[7],
            da[8],
            da[9],
            da[10],
            self.constants.base_critical_rate / 10000,
            da[17] or 0,
            da[11],
            self.lookup_member_by_id(da[0]),
            self.lookup_role_effect(da[6]),
            normal_appearance,
            idolized_appearance,
            self.lookup_active_skill_by_card_id(da[1]),
            self.lookup_passive_skills_by_card_id(da[1]),
            D.Card.LevelValues(1, *da[12:15]),
            self.tt_stat_increases.get(da[1]),
        )

        stats = self.connection.execute(
            """SELECT level, appeal, stamina, technique FROM m_card_parameter
                WHERE card_m_id = ? ORDER BY level""",
            (card_id,),
        )
        card.stats = [D.Card.LevelValues(*r) for r in stats]

        if da[15]:
            card.costume_info = D.Card.CostumeInfo(da[15], da[16], None, None)

        if not card.tt_offset:
            card.tt_offset = [D.Card.LevelValues(0, 0, 0, 0)]

        if use_cache:
            self.card_id_cache[card.id] = card

        return card

    def lookup_multiple_cards_by_id(self, idset: Sequence[int], briefs_ok=False):
        if len(idset) >= 192:
            cache = False
        else:
            cache = True

        retl = []
        for id in idset:
            if briefs_ok and id in self.card_brief_cache:
                retl.append(self.card_brief_cache[id])
            else:
                retl.append(self.lookup_card_by_id(id, cache))

        return retl

    def lookup_active_skill_by_card_id(self, card_id: int):
        EFFECT_1 = 11
        EFFECT_2 = 19
        EFFECT_COUNT = 8

        da = self.connection.execute(
            """SELECT m_active_skill.id, m_active_skill.name,
                m_active_skill.description, skill_type, trigger_probability, sp_gauge_point,
                m_active_skill.icon_asset_path, m_active_skill.thumbnail_asset_path,
                skill_target_master_id1, skill_target_master_id2, skill_effect_master_id2,

                _Se1.target_parameter,
                _Se1.effect_type, _Se1.effect_value,
                _Se1.scale_type, _Se1.calc_type,
                _Se1.timing,
                _Se1.finish_type, _Se1.finish_value,

                _Se2.target_parameter,
                _Se2.effect_type, _Se2.effect_value,
                _Se2.scale_type, _Se2.calc_type,
                _Se2.timing,
                _Se2.finish_type, _Se2.finish_value

                FROM m_card_active_skill
                LEFT JOIN m_active_skill ON (active_skill_master_id == m_active_skill.id)
                LEFT JOIN m_skill ON (m_active_skill.skill_master_id == m_skill.id)
                LEFT JOIN m_skill_effect AS _Se1 ON (m_skill.skill_effect_master_id1 == _Se1.id)
                LEFT JOIN m_skill_effect AS _Se2 ON (m_skill.skill_effect_master_id2 == _Se2.id)
                WHERE m_card_active_skill.card_master_id = ? ORDER BY skill_level""",
            (card_id,),
        )

        first = da.fetchone()
        if not first:
            return None

        target = self.lookup_skill_target_type(first[8])
        target_2 = None
        if first[9]:
            target_2 = self.lookup_skill_target_type(first[9])

        skill = D.Skill(
            first[0],
            first[1],
            first[2],
            first[3],
            first[5],
            first[6],
            first[7],
            0,
            TriggerType.Non,
            first[4],
            target,
            target_2,
        )

        # Levels
        skill.levels.append(D.Skill.Effect(*first[EFFECT_1 : EFFECT_1 + EFFECT_COUNT]))
        has_secondary_effect = first[10]
        if has_secondary_effect:
            skill.levels_2 = [D.Skill.Effect(*first[EFFECT_2 : EFFECT_2 + EFFECT_COUNT])]

        for remaining_row in da:
            skill.levels.append(D.Skill.Effect(*remaining_row[EFFECT_1 : EFFECT_1 + EFFECT_COUNT]))
            if has_secondary_effect:
                skill.levels_2.append(
                    D.Skill.Effect(*remaining_row[EFFECT_2 : EFFECT_2 + EFFECT_COUNT])
                )

        return skill

    def lookup_passive_skills_by_card_id(self, card_id: int):
        EFFECT_1 = 15
        EFFECT_2 = 23
        EFFECT_COUNT = 8

        da = self.connection.execute(
            """SELECT m_card_passive_skill_original.position, -- 0
                m_passive_skill.id, m_passive_skill.name, m_passive_skill.description, -- 2
                rarity, trigger_type, trigger_probability, -- 5
                m_passive_skill.icon_asset_path, m_passive_skill.thumbnail_asset_path, -- 7
                _Cd1.condition_type, _Cd1.condition_value, -- 9
                _Cd2.condition_type, _Cd2.condition_value, -- 11
                skill_target_master_id1, skill_target_master_id2, -- 13
                skill_effect_master_id2, -- 14

                _Se1.target_parameter,
                _Se1.effect_type, _Se1.effect_value,
                _Se1.scale_type, _Se1.calc_type,
                _Se1.timing,
                _Se1.finish_type, _Se1.finish_value,

                _Se2.target_parameter,
                _Se2.effect_type, _Se2.effect_value,
                _Se2.scale_type, _Se2.calc_type,
                _Se2.timing,
                _Se2.finish_type, _Se2.finish_value

                FROM m_card_passive_skill_original
                LEFT JOIN m_passive_skill ON (passive_skill_master_id == m_passive_skill.id)
                LEFT JOIN m_skill ON (m_passive_skill.skill_master_id == m_skill.id)
                LEFT JOIN m_skill_condition AS _Cd1 ON (m_passive_skill.skill_condition_master_id1 == _Cd1.id)
                LEFT JOIN m_skill_condition AS _Cd2 ON (m_passive_skill.skill_condition_master_id2 == _Cd2.id)

                LEFT JOIN m_skill_effect AS _Se1 ON (m_skill.skill_effect_master_id1 == _Se1.id)
                LEFT JOIN m_skill_effect AS _Se2 ON (m_skill.skill_effect_master_id2 == _Se2.id)
                WHERE m_card_passive_skill_original.card_master_id = ? ORDER BY position, skill_level""",
            (card_id,),
        )

        skills = []

        c_demux_key = None
        c_skill = None
        for demux_key, *row in da:
            if demux_key != c_demux_key:
                if c_skill:
                    skills.append(c_skill)

                c_skill = D.Skill(
                    row[0],
                    row[1],
                    row[2],
                    None,
                    None,
                    row[6],
                    row[7],
                    row[3],
                    row[4],
                    row[5],
                    self.lookup_skill_target_type(row[12]),
                    self.lookup_skill_target_type(row[13]) if row[13] else None,
                )

                if row[8] and row[8] != ConditionType.Non:
                    c_skill.conditions.append(D.Skill.Condition(row[8], row[9]))
                if row[10] and row[10] != ConditionType.Non:
                    c_skill.conditions.append(D.Skill.Condition(row[10], row[11]))
                if row[14]:
                    c_skill.levels_2 = []

                c_demux_key = demux_key

            c_skill.levels.append(D.Skill.Effect(*row[EFFECT_1 : EFFECT_1 + EFFECT_COUNT]))
            if row[13]:
                c_skill.levels_2.append(D.Skill.Effect(*row[EFFECT_2 : EFFECT_2 + EFFECT_COUNT]))

        if c_skill:
            skills.append(c_skill)

        return skills

    def lookup_song_list(self):
        da = self.connection.execute(
            """SELECT live_id, name, member_group, member_unit, jacket_asset_path,
                m_member_group.group_name, m_member_unit.unit_name,
                m_live.display_order FROM m_live
            LEFT JOIN m_member_group USING (member_group)
            LEFT JOIN m_member_unit USING (member_unit)
            ORDER BY m_live.display_order"""
        )

        return [D.Live(*row) for row in da]

    def lookup_song_difficulties(self, for_song_id: int):
        da = self.connection.execute(
            """SELECT name, member_group, member_unit, jacket_asset_path,
                m_member_group.group_name, m_member_unit.unit_name,
                m_live.display_order FROM m_live
            LEFT JOIN m_member_group USING (member_group)
            LEFT JOIN m_member_unit USING (member_unit)
            WHERE live_id = ? LIMIT 1""",
            (for_song_id,),
        )

        root = D.Live(for_song_id, *da.fetchone())
        da.close()

        da = self.connection.execute(
            """SELECT live_difficulty_id, live_difficulty_type,
                evaluation_s_score, evaluation_a_score, evaluation_b_score, evaluation_c_score,
                recommended_score, recommended_stamina,
                sp_gauge_length, note_stamina_reduce, note_voltage_upper_limit

                FROM m_live_difficulty
                LEFT JOIN m_live_difficulty_const ON (live_difficulty_id = m_live_difficulty_const.id)
                WHERE m_live_difficulty.live_id = ?
                ORDER BY live_difficulty_type""",
            (for_song_id,),
        )

        diffs = []
        for row in da:
            the_diff = D.LiveDifficulty(*row)
            the_diff.stage_gimmicks = self.lookup_gimmicks_by_live_diff_id(the_diff.id)
            the_diff.note_gimmicks = self.lookup_note_gimmicks_by_live_diff_id(the_diff.id)
            the_diff.wave_missions = self.lookup_wave_descriptions_for_live_id(the_diff.id)
            diffs.append(the_diff)
        root.difficulties = diffs
        return root

    def lookup_note_gimmicks_by_live_diff_id(self, live_diff_id: int):
        EFFECT_1 = 6
        EFFECT_2 = 14
        EFFECT_COUNT = 8

        da = self.connection.execute(
            """SELECT COUNT(0), m_live_difficulty_note_gimmick.name, m_live_difficulty_note_gimmick.description,
                skill_target_master_id1, skill_target_master_id2, skill_effect_master_id2,

                _Se1.target_parameter,
                _Se1.effect_type, _Se1.effect_value,
                _Se1.scale_type, _Se1.calc_type,
                _Se1.timing, _Se1.finish_type, _Se1.finish_value,

                _Se2.target_parameter,
                _Se2.effect_type, _Se2.effect_value,
                _Se2.scale_type, _Se2.calc_type,
                _Se2.timing, _Se2.finish_type, _Se2.finish_value

                FROM m_live_difficulty_note_gimmick
                LEFT JOIN m_skill ON (m_live_difficulty_note_gimmick.skill_master_id == m_skill.id)
                LEFT JOIN m_skill_effect AS _Se1 ON (m_skill.skill_effect_master_id1 == _Se1.id)
                LEFT JOIN m_skill_effect AS _Se2 ON (m_skill.skill_effect_master_id2 == _Se2.id)
                WHERE m_live_difficulty_note_gimmick.live_difficulty_id = ?
                GROUP BY skill_master_id""",
            (live_diff_id,),
        )

        skills = []
        for row in da:
            c_skill = D.Skill(
                row[0],
                row[1],
                row[2],
                None,
                None,
                None,
                None,
                None,
                None,
                10000,
                self.lookup_skill_target_type(row[3]),
                self.lookup_skill_target_type(row[4]) if row[4] else None,
            )
            c_skill.levels.append(D.Skill.Effect(*row[EFFECT_1 : EFFECT_1 + EFFECT_COUNT]))
            if row[5]:
                c_skill.levels_2 = [D.Skill.Effect(*row[EFFECT_2 : EFFECT_2 + EFFECT_COUNT])]
            skills.append(c_skill)

        return skills

    def lookup_gimmicks_by_live_diff_id(self, live_diff_id: int):
        EFFECT_1 = 11
        EFFECT_2 = 19
        EFFECT_COUNT = 8

        da = self.connection.execute(
            """SELECT m_live_difficulty_gimmick.id, m_live_difficulty_gimmick.name,
                m_live_difficulty_gimmick.description, trigger_type,
                _Cd1.condition_type, _Cd1.condition_value, -- 5
                _Cd2.condition_type, _Cd2.condition_value, -- 7
                skill_target_master_id1, skill_target_master_id2, skill_effect_master_id2, -- 10

                _Se1.target_parameter,
                _Se1.effect_type, _Se1.effect_value,
                _Se1.scale_type, _Se1.calc_type,
                _Se1.timing, _Se1.finish_type, _Se1.finish_value,

                _Se2.target_parameter,
                _Se2.effect_type, _Se2.effect_value,
                _Se2.scale_type, _Se2.calc_type,
                _Se2.timing, _Se2.finish_type, _Se2.finish_value

                FROM m_live_difficulty_gimmick
                LEFT JOIN m_skill ON (m_live_difficulty_gimmick.skill_master_id == m_skill.id)
                LEFT JOIN m_skill_condition AS _Cd1 ON (m_live_difficulty_gimmick.condition_master_id1 == _Cd1.id)
                LEFT JOIN m_skill_condition AS _Cd2 ON (m_live_difficulty_gimmick.condition_master_id2 == _Cd2.id)
                LEFT JOIN m_skill_effect AS _Se1 ON (m_skill.skill_effect_master_id1 == _Se1.id)
                LEFT JOIN m_skill_effect AS _Se2 ON (m_skill.skill_effect_master_id2 == _Se2.id)
                WHERE m_live_difficulty_gimmick.live_difficulty_master_id = ? AND trigger_type < 255""",
            (live_diff_id,),
        )

        skills = []
        for row in da:
            c_skill = D.Skill(
                row[0],
                row[1],
                row[2],
                None,
                None,
                None,
                None,
                None,
                row[3],
                10000,
                self.lookup_skill_target_type(row[8]),
                self.lookup_skill_target_type(row[9]) if row[9] else None,
            )

            if row[4] and row[4] != ConditionType.Non:
                c_skill.conditions.append(D.Skill.Condition(row[4], row[5]))
            if row[6] and row[6] != ConditionType.Non:
                c_skill.conditions.append(D.Skill.Condition(row[6], row[7]))

            c_skill.levels.append(D.Skill.Effect(*row[EFFECT_1 : EFFECT_1 + EFFECT_COUNT]))
            if row[10]:
                c_skill.levels_2 = [D.Skill.Effect(*row[EFFECT_2 : EFFECT_2 + EFFECT_COUNT])]
            skills.append(c_skill)

        return skills

    def _lookup_generic_skill_info(self, skill_id: int, cons: type):
        EFFECT_1 = 4
        EFFECT_2 = 12
        EFFECT_COUNT = 8
        da = self.connection.execute(
            """SELECT m_skill.id,
                skill_target_master_id1, skill_target_master_id2, skill_effect_master_id2,

                _Se1.target_parameter,
                _Se1.effect_type, _Se1.effect_value,
                _Se1.scale_type, _Se1.calc_type,
                _Se1.timing, _Se1.finish_type, _Se1.finish_value,

                _Se2.target_parameter,
                _Se2.effect_type, _Se2.effect_value,
                _Se2.scale_type, _Se2.calc_type,
                _Se2.timing, _Se2.finish_type, _Se2.finish_value

                FROM m_skill
                LEFT JOIN m_skill_effect AS _Se1 ON (m_skill.skill_effect_master_id1 == _Se1.id)
                LEFT JOIN m_skill_effect AS _Se2 ON (m_skill.skill_effect_master_id2 == _Se2.id)
                WHERE m_skill.id = ? LIMIT 1""",
            (skill_id,),
        )
        row = da.fetchone()

        if not row:
            return None

        c_skill = cons(
            row[0],
            "DUMMY",
            "DUMMY",
            None,
            None,
            None,
            None,
            None,
            TriggerType.Non,
            10000,
            self.lookup_skill_target_type(row[1]),
            self.lookup_skill_target_type(row[2]) if row[2] else None,
        )

        c_skill.levels.append(D.Skill.Effect(*row[EFFECT_1 : EFFECT_1 + EFFECT_COUNT]))
        if row[3]:
            c_skill.levels_2 = [D.Skill.Effect(*row[EFFECT_2 : EFFECT_2 + EFFECT_COUNT])]
        return c_skill

    def lookup_wave_descriptions_for_live_id(self, live_diff_id: int):
        da = self.connection.execute(
            """SELECT wave_id, name, description, skill_id, state
                FROM m_live_note_wave_gimmick_group
                WHERE live_difficulty_id = ?
                ORDER BY wave_id""",
            (live_diff_id,),
        )

        rlist = []
        for id, name, desc, skillid, state in da.fetchall():
            mission = D.LiveWaveMission(id, name, desc, LANGUAGE_DEFINITION_JA)

            if state < 255:
                gimmick = self._lookup_generic_skill_info(skillid, D.LiveWaveMission.Gimmick)
                gimmick.wave_state = state
                mission.gimmick = gimmick

            rlist.append(mission)

        return rlist

    def lookup_all_accessory_skills(self):
        EFFECT_1 = 15
        EFFECT_2 = 23
        EFFECT_COUNT = 8
        da = self.connection.execute(
            """SELECT m_accessory_passive_skill.id,
                name, description, rarity, trigger_type, probability_at_level_min,
                m_accessory_passive_skill.icon_asset_path, m_accessory_passive_skill.thumbnail_asset_path,
                _Cd1.condition_type, _Cd1.condition_value,
                _Cd2.condition_type, _Cd2.condition_value,
                skill_target_master_id1, skill_target_master_id2, skill_effect_master_id2,

                _Se1.target_parameter,
                _Se1.effect_type, _Se1.effect_value,
                _Se1.scale_type, _Se1.calc_type,
                _Se1.timing, _Se1.finish_type, _Se1.finish_value,

                _Se2.target_parameter,
                _Se2.effect_type, _Se2.effect_value,
                _Se2.scale_type, _Se2.calc_type,
                _Se2.timing, _Se2.finish_type, _Se2.finish_value

                FROM m_accessory_passive_skill
                LEFT JOIN m_accessory_passive_skill_level ON
                    (m_accessory_passive_skill_level.accessory_passive_skill_master_id
                        == m_accessory_passive_skill.id AND skill_level == 1)
                LEFT JOIN m_skill ON (m_accessory_passive_skill.skill_master_id == m_skill.id)
                LEFT JOIN m_skill_condition AS _Cd1 ON (m_accessory_passive_skill.skill_condition_master_id1 == _Cd1.id)
                LEFT JOIN m_skill_condition AS _Cd2 ON (m_accessory_passive_skill.skill_condition_master_id2 == _Cd2.id)
                LEFT JOIN m_skill_effect AS _Se1 ON (m_skill.skill_effect_master_id1 == _Se1.id)
                LEFT JOIN m_skill_effect AS _Se2 ON (m_skill.skill_effect_master_id2 == _Se2.id)
                ORDER BY m_accessory_passive_skill.id"""
        )

        skills = []
        for row in da:
            skill = D.Skill(
                row[0],
                row[1],
                row[2],
                None,
                None,
                row[6],
                row[7],
                row[3],
                row[4],
                row[5],
                self.lookup_skill_target_type(row[12]),
                self.lookup_skill_target_type(row[13]) if row[13] else None,
            )
            if row[8] and row[8] != ConditionType.Non:
                skill.conditions.append(D.Skill.Condition(row[8], row[9]))
            if row[10] and row[10] != ConditionType.Non:
                skill.conditions.append(D.Skill.Condition(row[10], row[11]))

            skill.levels.append(D.Skill.Effect(*row[EFFECT_1 : EFFECT_1 + EFFECT_COUNT]))
            if row[14]:
                skill.levels_2 = [D.Skill.Effect(*row[EFFECT_2 : EFFECT_2 + EFFECT_COUNT])]
            skills.append(skill)

        return skills

    def lookup_all_hirameku_skills(self):
        EFFECT_1 = 15
        EFFECT_2 = 23
        EFFECT_COUNT = 8
        da = self.connection.execute(
            """SELECT m_passive_skill.id,
                name, description, rarity, trigger_type, trigger_probability,
                m_passive_skill.icon_asset_path, m_passive_skill.thumbnail_asset_path,
                _Cd1.condition_type, _Cd1.condition_value,
                _Cd2.condition_type, _Cd2.condition_value,
                skill_target_master_id1, skill_target_master_id2, skill_effect_master_id2,

                _Se1.target_parameter,
                _Se1.effect_type, _Se1.effect_value,
                _Se1.scale_type, _Se1.calc_type,
                _Se1.timing, _Se1.finish_type, _Se1.finish_value,

                _Se2.target_parameter,
                _Se2.effect_type, _Se2.effect_value,
                _Se2.scale_type, _Se2.calc_type,
                _Se2.timing, _Se2.finish_type, _Se2.finish_value

                FROM m_passive_skill
                LEFT JOIN m_skill ON (m_passive_skill.skill_master_id == m_skill.id)
                LEFT JOIN m_skill_condition as _Cd1 ON (m_passive_skill.skill_condition_master_id1 == _Cd1.id)
                LEFT JOIN m_skill_condition as _Cd2 ON (m_passive_skill.skill_condition_master_id2 == _Cd2.id)
                LEFT JOIN m_skill_effect AS _Se1 ON (m_skill.skill_effect_master_id1 == _Se1.id)
                LEFT JOIN m_skill_effect AS _Se2 ON (m_skill.skill_effect_master_id2 == _Se2.id)
                WHERE m_passive_skill.id > 30000000
                ORDER BY m_passive_skill.id"""
        ).fetchall()

        skills = []
        for row in da:
            skill = D.Skill(
                row[0],
                row[1],
                row[2],
                None,
                None,
                row[6],
                row[7],
                row[3],
                row[4],
                row[5],
                self.lookup_skill_target_type(row[12]),
                self.lookup_skill_target_type(row[13]) if row[13] else None,
            )
            if row[8] and row[8] != ConditionType.Non:
                skill.conditions.append(D.Skill.Condition(row[8], row[9]))
            if row[10] and row[10] != ConditionType.Non:
                skill.conditions.append(D.Skill.Condition(row[10], row[11]))

            skill.levels.append(D.Skill.Effect(*row[EFFECT_1 : EFFECT_1 + EFFECT_COUNT]))
            if row[14]:
                skill.levels_2 = [D.Skill.Effect(*row[EFFECT_2 : EFFECT_2 + EFFECT_COUNT])]
            skills.append(skill)

        return skills

    @lru_cache(4)
    def lookup_role_effect(self, role_id):
        row = self.connection.execute(
            "SELECT * FROM m_card_role_effect WHERE id = ?",
            (role_id,),
        ).fetchone()

        if not row:
            return None

        return D.Card.RoleEffect(*row[1:])

    @lru_cache(maxsize=None)
    def lookup_skill_target_type(self, stid):
        basic = self.connection.execute(
            "SELECT * FROM m_skill_target WHERE id = ? LIMIT 1", (stid,)
        ).fetchone()
        if not basic:
            return None

        target_type = D.Skill.TargetType(
            basic["id"],
            basic["only_owner"],
            basic["excluding_owner"],
            basic["random_choose_count"],
            basic["checking_owner_party"],
            basic["checking_owner_school"],
            basic["checking_owner_grade"],
            basic["checking_owner_unit"],
            basic["checking_owner_attribute"],
            basic["checking_owner_role"],
        )

        if basic["target_attribute_group_id"]:
            group = self.connection.execute(
                "SELECT attribute FROM m_skill_target_attribute_group WHERE group_id = ?",
                (basic["target_attribute_group_id"],),
            ).fetchall()
            target_type.fixed_attributes.extend(x[0] for x in group)
        if basic["target_member_group_id"]:
            group = self.connection.execute(
                "SELECT member_maseter_id FROM m_skill_target_member_group WHERE group_id = ? LIMIT 1",
                (basic["target_member_group_id"],),
            ).fetchall()
            target_type.fixed_members.extend(x[0] for x in group)
        if basic["target_unit_group_id"]:
            group = self.connection.execute(
                "SELECT member_unit FROM m_skill_target_unit_group WHERE group_id = ? LIMIT 1",
                (basic["target_unit_group_id"],),
            ).fetchall()
            target_type.fixed_subunits.extend(x[0] for x in group)
        if basic["target_school_group_id"]:
            group = self.connection.execute(
                "SELECT member_group FROM m_skill_target_school_group WHERE group_id = ? LIMIT 1",
                (basic["target_school_group_id"],),
            ).fetchall()
            target_type.fixed_schools.extend(x[0] for x in group)
        if basic["target_school_grade_group_id"]:
            group = self.connection.execute(
                "SELECT grade FROM m_skill_target_school_grade_group WHERE group_id = ? LIMIT 1",
                (basic["target_school_grade_group_id"],),
            ).fetchall()
            target_type.fixed_years.extend(x[0] for x in group)
        if basic["target_role_group_id"]:
            group = self.connection.execute(
                "SELECT role FROM m_skill_target_cardrole_group WHERE group_id = ? LIMIT 1",
                (basic["target_role_group_id"],),
            ).fetchall()
            target_type.fixed_roles.extend(x[0] for x in group)
        return target_type

    def lookup_batch_item_req_set(self, item_set_ids: Iterable[int]):
        id_list = ",".join(str(int(x)) for x in set(item_set_ids))

        rows = self.connection.execute(
            f"""SELECT m_training_tree_cell_item_set.id, content_type, content_id,
                content_amount, thumbnail_asset_path, display_order
            FROM m_training_tree_cell_item_set
            LEFT JOIN m_training_material ON
                (content_type == 12 AND content_id == m_training_material.id)
            WHERE m_training_tree_cell_item_set.id IN ({id_list})
            ORDER BY m_training_tree_cell_item_set.id"""
        )

        items = {}
        struct = defaultdict(lambda: defaultdict())
        for (
            group,
            content_type,
            content_id,
            content_amount,
            thumbnail_asset_path,
            display_order,
        ) in rows:
            if content_type == 12:
                items[str(content_id)] = (thumbnail_asset_path, display_order)
                struct[group][str(content_id)] = content_amount
            else:
                struct[group]["_gold"] = content_amount
        return {"items": items, "sets": struct}

    def lookup_tt(self, ttid):
        tree = self.connection.execute(
            """SELECT training_tree_cell_content_m_id, training_tree_design_m_id, training_tree_card_param_m_id
            FROM m_training_tree
            LEFT JOIN m_training_tree_mapping ON (training_tree_mapping_m_id = m_training_tree_mapping.id)
            WHERE m_training_tree.id = ? LIMIT 1""",
            (ttid,),
        ).fetchone()
        if not tree:
            return None

        content_track_id, shape_id, card_params = tree
        # We only care about stat increases for now...
        entries = self.connection.execute(
            """SELECT m_training_tree_design.cell_id, parent_cell_id,
                parent_branch_type,
                training_tree_cell_type, required_grade,
                training_content_type, value,
                training_tree_cell_item_set_m_id
            FROM m_training_tree_design
            LEFT JOIN m_training_tree_cell_content ON
                (m_training_tree_design.cell_id = m_training_tree_cell_content.cell_id
                AND m_training_tree_cell_content.id = ?)
            LEFT JOIN m_training_tree_card_param ON
                (m_training_tree_card_param.training_content_no = m_training_tree_cell_content.training_content_no
                AND training_tree_cell_type = 2
                AND m_training_tree_card_param.id = ?)
            WHERE m_training_tree_design.id = ? ORDER BY m_training_tree_design.cell_id""",
            (content_track_id, card_params, shape_id),
        ).fetchall()

        if entries:
            item_sets = self.lookup_batch_item_req_set(e[-1] for e in entries if e)
            return (item_sets, *construct_tt_from_sql_shape(entries))

        return None

    def lookup_costumes(self, member_id):
        rets = OrderedDict()
        suits = self.connection.execute(
            """SELECT name, id, thumbnail_image_asset_path FROM m_suit 
            WHERE member_m_id = ? ORDER BY display_order""",
            (member_id,),
        )
        for name, id, thumb in suits:
            rets[id] = D.Card.CostumeInfo(thumb, id, name, [])

        suit_alt_views = self.connection.execute(
            """SELECT suit_master_id, view_status FROM m_suit_view 
            LEFT JOIN m_suit ON (suit_master_id = id)
            WHERE member_m_id = ? ORDER BY view_status""",
            (member_id,),
        )
        for id, variant in suit_alt_views:
            rets[id].variants.append(variant)

        return rets
