import os
import sqlite3
from collections import defaultdict
from functools import lru_cache
from typing import Iterable, Sequence

from cachetools import LFUCache

from . import dataclasses as D
from .utils import construct_tt_from_sql_shape
from .wave_description_base import LANGUAGE_DEFINITION_JA


class MasterData(object):
    def __init__(self, master_path):
        self.version = os.path.basename(master_path.rstrip("/"))
        self.connection = sqlite3.connect(
            "file:{0}?mode=ro".format(os.path.join(master_path, "masterdata.db")), uri=True
        )
        self.connection.row_factory = sqlite3.Row
        self.card_id_cache = LFUCache(256)
        self.member_cache = {}

        self.ordinal_to_cid = {
            ord: id for ord, id in self.connection.execute("SELECT school_idol_no, id FROM m_card")
        }
        self.tt_stat_increases = self.distill_tt_stat_increases()
        print(f"MasterData: alloc with {len(self.ordinal_to_cid)} cards")

    def distill_tt_stat_increases(self):
        rs = self.connection.execute(
            """
            SELECT m_card.id AS demux, training_content_type, required_grade, SUM(value)
            FROM m_card
            LEFT JOIN m_training_tree ON (m_training_tree.id = m_card.training_tree_m_id)
            LEFT JOIN m_training_tree_card_param ON (m_training_tree.training_tree_card_param_m_id = m_training_tree_card_param.id)
            LEFT JOIN m_training_tree_mapping ON (m_training_tree.training_tree_mapping_m_id = m_training_tree_mapping.id)
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
            ls.append(D.CardLevelValues(k, a, s, t))
        return ls

    def lookup_member_by_id(self, member_id: int):
        if member_id in self.member_cache:
            return self.member_cache[member_id]

        da = self.connection.execute(
            """
        SELECT m_member.id, member_group, m_member_unit.member_unit AS subunit, school_grade AS year, name,
        name_romaji, birth_month, birth_day, m_member.theme_dark_color,

        m_member_group.group_name, m_member_unit.unit_name,

        thumbnail_image_asset_path,
        standing_image_asset_path, autograph_image_asset_path,
        member_icon_image_asset_path FROM m_member
        LEFT JOIN m_member_group USING (member_group)
        LEFT JOIN m_member_unit_detail ON (m_member_unit_detail.member_m_id == m_member.id)
        LEFT JOIN m_member_unit ON (m_member_unit_detail.member_unit == m_member_unit.member_unit)
        WHERE m_member.id = ? LIMIT 1
        """,
            (member_id,),
        ).fetchone()

        if not da:
            return None

        m = D.Member(*da)

        da = self.connection.execute(
            """
        SELECT id, school_idol_no, card_rarity_type, card_attribute,
        role, thumbnail_asset_path
        FROM m_card
        LEFT JOIN m_card_appearance ON (card_m_id = m_card.id AND appearance_type == 1)
        WHERE member_m_id = ? ORDER BY m_card.school_idol_no DESC
        """,
            (member_id,),
        )

        m.card_brief = [D.CardLite(*row[:5], D.CardAppearance(None, None, row[5])) for row in da]

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
            f"""
        SELECT m_member.id FROM m_member
        LEFT JOIN m_member_unit_detail ON (m_member_unit_detail.member_m_id == m_member.id)
        LEFT JOIN m_member_unit ON (m_member_unit_detail.member_unit == m_member_unit.member_unit)
        {where}
        ORDER BY member_group, m_member_unit.member_unit, m_member.id""",
            {"unit": subunit, "group": group},
        )

        return [self.lookup_member_by_id(i) for i, in ids]

    def do_not_use_get_all_card_briefs(self):
        da = self.connection.execute(
            """SELECT id, school_idol_no, card_rarity_type, card_attribute,
                role, thumbnail_asset_path
                FROM m_card
                LEFT JOIN m_card_appearance ON (card_m_id = m_card.id AND appearance_type == 1)
                ORDER BY m_card.school_idol_no"""
        )

        return [D.CardLite(*row[:5], D.CardAppearance(None, None, row[5])) for row in da]

    def all_ordinals(self):
        return sorted(self.ordinal_to_cid.keys())

    def card_ordinals_to_ids(self, ordinals: Iterable[int]):
        return [self.ordinal_to_cid.get(o) for o in ordinals]

    def lookup_card_by_id(self, card_id: int, use_cache: bool = True):
        if card_id in self.card_id_cache:
            return self.card_id_cache[card_id]

        da = self.connection.execute(
            """
        SELECT member_m_id, id, school_idol_no, card_rarity_type, max_level, card_attribute,
        role, training_tree_m_id, sp_point, exchange_item_id, max_passive_skill_slot,
        m_card_attribute.background_asset_path, 0, parameter2, parameter1, parameter3
        FROM m_card
        LEFT JOIN m_card_rarity USING (card_rarity_type)
        LEFT JOIN m_card_attribute USING (card_attribute)
        LEFT JOIN m_card_awaken_parameter ON (card_master_id == m_card.id)
        WHERE m_card.id = ? LIMIT 1
        """,
            (card_id,),
        ).fetchone()

        if not da:
            return None
        member_id, *da = da
        card = D.Card(*da[:11])
        card.member = self.lookup_member_by_id(member_id)
        card.active_skill = self.lookup_active_skill_by_card_id(card.id)
        card.passive_skills = self.lookup_passive_skills_by_card_id(card.id)
        card.idolized_offset = D.CardLevelValues(*da[11:])
        card.tt_offset = self.tt_stat_increases.get(card.id)
        card.role_effect = self.lookup_role_effect(card.role)

        if not card.tt_offset:
            card.tt_offset = D.CardLevelValues(0, 0, 0, 0)

        stats = self.connection.execute(
            """SELECT level, appeal, stamina, technique FROM
        m_card_parameter WHERE card_m_id = ? ORDER BY level
        """,
            (card_id,),
        )
        card.stats = [D.CardLevelValues(*r) for r in stats]

        appearances = self.connection.execute(
            """
        SELECT appearance_type, card_name, image_asset_path, thumbnail_asset_path FROM m_card_appearance
        WHERE card_m_id = ? ORDER BY appearance_type LIMIT 2
        """,
            (da[0],),
        ).fetchall()
        for type_, *row in appearances:
            if type_ == 1:
                card.normal_appearance = D.CardAppearance(*row)
            if type_ == 2:
                card.idolized_appearance = D.CardAppearance(*row)

        if use_cache:
            self.card_id_cache[card.id] = card

        return card

    def lookup_multiple_cards_by_id(self, idset: Sequence[int]):
        if len(idset) >= 192:
            cache = False
        else:
            cache = True

        return [self.lookup_card_by_id(i, cache) for i in idset]

    def lookup_active_skill_by_card_id(self, card_id: int):
        ROOT_COUNT = 8

        da = self.connection.execute(
            """
        SELECT skill_target_master_id1, m_active_skill.id, m_active_skill.name, m_active_skill.description,
        skill_type, trigger_probability, sp_gauge_point,
        m_active_skill.icon_asset_path, m_active_skill.thumbnail_asset_path,
        m_skill_effect.* FROM m_card_active_skill
        LEFT JOIN m_active_skill ON (active_skill_master_id == m_active_skill.id)
        LEFT JOIN m_skill ON (m_active_skill.skill_master_id == m_skill.id)
        LEFT JOIN m_skill_effect ON (m_skill.skill_effect_master_id1 == m_skill_effect.id)
        WHERE m_card_active_skill.card_master_id = ? ORDER BY skill_level
        """,
            (card_id,),
        )

        root = da.fetchone()
        if not root:
            return None

        target_id, *root = root
        skill = D.ActiveSkill(*root[:ROOT_COUNT])
        skill.levels = [root[ROOT_COUNT:]]
        for _, *level in da:
            skill.levels.append(level[ROOT_COUNT:])

        skill.target = self.lookup_skill_target_type(target_id)
        return skill

    def lookup_passive_skills_by_card_id(self, card_id: int):
        ROOT_COUNT = 10

        da = self.connection.execute(
            """
        SELECT skill_target_master_id1, m_card_passive_skill_original.position,
        m_passive_skill.id, m_passive_skill.name, m_passive_skill.description,
        rarity, trigger_type, trigger_probability,
        m_passive_skill.icon_asset_path, m_passive_skill.thumbnail_asset_path,
        condition_type, condition_value,
        m_skill_effect.* FROM m_card_passive_skill_original
        LEFT JOIN m_passive_skill ON (passive_skill_master_id == m_passive_skill.id)
        LEFT JOIN m_skill ON (m_passive_skill.skill_master_id == m_skill.id)
        LEFT JOIN m_skill_condition ON (m_passive_skill.skill_condition_master_id1 == m_skill_condition.id)
        LEFT JOIN m_skill_effect ON (m_skill.skill_effect_master_id1 == m_skill_effect.id)
        WHERE m_card_passive_skill_original.card_master_id = ? ORDER BY position, skill_level
        """,
            (card_id,),
        )

        skills = []
        c_demux_key = None
        c_skill = None
        for target_id, demux_key, *actual in da:
            if demux_key != c_demux_key:
                if c_skill:
                    skills.append(c_skill)
                c_skill = D.PassiveSkill(*actual[:ROOT_COUNT])
                c_skill.target = self.lookup_skill_target_type(target_id)
                c_skill.levels = []
                c_demux_key = demux_key
            c_skill.levels.append(actual[ROOT_COUNT:])

        if c_skill:
            skills.append(c_skill)

        return skills

    def lookup_song_list(self):
        da = self.connection.execute(
            """
        SELECT live_id, name, member_group, member_unit, jacket_asset_path,
            m_member_group.group_name, m_member_unit.unit_name,
            m_live.display_order FROM m_live
        LEFT JOIN m_member_group USING (member_group)
        LEFT JOIN m_member_unit USING (member_unit)
        ORDER BY m_live.display_order"""
        )

        return [D.Live(*row) for row in da]

    def lookup_song_difficulties(self, for_song_id: int):
        da = self.connection.execute(
            """
        SELECT name, member_group, member_unit, jacket_asset_path,
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
            """
        SELECT live_difficulty_id,
            live_difficulty_type,
            evaluation_s_score,
            evaluation_a_score,
            evaluation_b_score,
            evaluation_c_score
        FROM m_live_difficulty
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
        ROOT_COUNT = 9

        da = self.connection.execute(
            """
        SELECT skill_target_master_id1,
        COUNT(0),
        m_live_difficulty_note_gimmick.name,
        m_live_difficulty_note_gimmick.description,
        0, 10000, 0, 0,
        NULL, NULL,
        m_skill_effect.* FROM m_live_difficulty_note_gimmick

        LEFT JOIN m_skill ON (m_live_difficulty_note_gimmick.skill_master_id == m_skill.id)
        LEFT JOIN m_skill_effect ON (m_skill.skill_effect_master_id1 == m_skill_effect.id)
        WHERE m_live_difficulty_note_gimmick.live_difficulty_id = ?
        GROUP BY skill_master_id
        """,
            (live_diff_id,),
        )

        skills = []
        for target_id, *actual in da:
            c_skill = D.ActiveSkill(*actual[:ROOT_COUNT])
            c_skill.target = self.lookup_skill_target_type(target_id)
            c_skill.levels = [actual[ROOT_COUNT:]]
            skills.append(c_skill)

        return skills

    def lookup_gimmicks_by_live_diff_id(self, live_diff_id: int):
        ROOT_COUNT = 10

        da = self.connection.execute(
            """
        SELECT skill_target_master_id1,
        m_live_difficulty_gimmick.id,
        m_live_difficulty_gimmick.name,
        m_live_difficulty_gimmick.description,
        0, trigger_type, 10000, NULL, NULL,
        condition_type, condition_value,
        m_skill_effect.* FROM m_live_difficulty_gimmick

        LEFT JOIN m_skill ON (m_live_difficulty_gimmick.skill_master_id == m_skill.id)
        LEFT JOIN m_skill_condition ON (m_live_difficulty_gimmick.condition_master_id1 == m_skill_condition.id)
        LEFT JOIN m_skill_effect ON (m_skill.skill_effect_master_id1 == m_skill_effect.id)
        WHERE m_live_difficulty_gimmick.live_difficulty_master_id = ?
        """,
            (live_diff_id,),
        )

        skills = []
        for target_id, *actual in da:
            c_skill = D.PassiveSkill(*actual[:ROOT_COUNT])
            c_skill.target = self.lookup_skill_target_type(target_id)
            c_skill.levels = [actual[ROOT_COUNT:]]
            skills.append(c_skill)

        return skills

    def lookup_wave_descriptions_for_live_id(self, live_diff_id: int):
        da = self.connection.execute(
            """SELECT wave_id, name, description
            FROM m_live_note_wave_gimmick_group
            WHERE live_difficulty_id = ?
            ORDER BY wave_id""",
            (live_diff_id,),
        )
        return [D.LiveWaveMission(*x, LANGUAGE_DEFINITION_JA) for x in da.fetchall()]

    def lookup_all_accessory_skills(self):
        da = self.connection.execute(
            """
        SELECT skill_target_master_id1, m_accessory_passive_skill.id,
        name, description, rarity, trigger_type, probability_at_level_min,
        m_accessory_passive_skill.icon_asset_path, m_accessory_passive_skill.thumbnail_asset_path,
        condition_type, condition_value,
        m_skill_effect.* FROM m_accessory_passive_skill
        LEFT JOIN m_accessory_passive_skill_level ON
            (m_accessory_passive_skill_level.accessory_passive_skill_master_id
                == m_accessory_passive_skill.id AND skill_level == 1)
        LEFT JOIN m_skill ON (m_accessory_passive_skill.skill_master_id == m_skill.id)
        LEFT JOIN m_skill_condition ON (m_accessory_passive_skill.skill_condition_master_id1 == m_skill_condition.id)
        LEFT JOIN m_skill_effect ON (m_skill.skill_effect_master_id1 == m_skill_effect.id)
        ORDER BY m_accessory_passive_skill.id
        """
        )

        skills = []
        for target_id, *row in da:
            skill = D.PassiveSkill(*row[:10])
            skill.levels = [row[10:]]
            skill.target = self.lookup_skill_target_type(target_id)
            skills.append(skill)

        return skills

    def lookup_all_hirameku_skills(self):
        da = self.connection.execute(
            """
        SELECT skill_target_master_id1, m_passive_skill.id,
        name, description, rarity, trigger_type, trigger_probability,
        m_passive_skill.icon_asset_path, m_passive_skill.thumbnail_asset_path,
        condition_type, condition_value,
        m_skill_effect.* FROM m_passive_skill
        LEFT JOIN m_skill ON (m_passive_skill.skill_master_id == m_skill.id)
        LEFT JOIN m_skill_condition ON (m_passive_skill.skill_condition_master_id1 == m_skill_condition.id)
        LEFT JOIN m_skill_effect ON (m_skill.skill_effect_master_id1 == m_skill_effect.id)
        WHERE m_passive_skill.id > 30000000
        ORDER BY m_passive_skill.id
        """
        ).fetchall()

        skills = []
        for target_id, *row in da:
            skill = D.PassiveSkill(*row[:10])
            skill.levels = [row[10:]]
            skill.target = self.lookup_skill_target_type(target_id)
            skills.append(skill)

        return skills

    @lru_cache(4)
    def lookup_role_effect(self, role_id):
        da = self.connection.execute(
            """
        SELECT * FROM m_card_role_effect WHERE id = ?
        """,
            (role_id,),
        ).fetchone()

        if not da:
            return None

        return D.CardRoleEffect(*da[1:])

    @lru_cache(maxsize=None)
    def lookup_skill_target_type(self, stid):
        basic = self.connection.execute(
            "SELECT * FROM m_skill_target WHERE id = ? LIMIT 1", (stid,)
        ).fetchone()
        if not basic:
            return None

        target_type = D.SkillTargetType(
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
                """SELECT attribute FROM m_skill_target_attribute_group
            WHERE group_id = ?""",
                (basic["target_attribute_group_id"],),
            ).fetchall()
            target_type.fixed_attributes = [x[0] for x in group]
        if basic["target_member_group_id"]:
            group = self.connection.execute(
                """SELECT member_maseter_id FROM m_skill_target_member_group
            WHERE group_id = ? LIMIT 1""",
                (basic["target_member_group_id"],),
            ).fetchall()
            target_type.fixed_members = [x[0] for x in group]
        if basic["target_unit_group_id"]:
            group = self.connection.execute(
                """SELECT member_unit FROM m_skill_target_unit_group
            WHERE group_id = ? LIMIT 1""",
                (basic["target_unit_group_id"],),
            ).fetchall()
            target_type.fixed_subunits = [x[0] for x in group]
        if basic["target_school_group_id"]:
            group = self.connection.execute(
                """SELECT member_group FROM m_skill_target_school_group
            WHERE group_id = ? LIMIT 1""",
                (basic["target_school_group_id"],),
            ).fetchall()
            target_type.fixed_schools = [x[0] for x in group]
        if basic["target_school_grade_group_id"]:
            group = self.connection.execute(
                """SELECT grade FROM m_skill_target_school_grade_group
            WHERE group_id = ? LIMIT 1""",
                (basic["target_school_grade_group_id"],),
            ).fetchall()
            target_type.fixed_years = [x[0] for x in group]
        if basic["target_role_group_id"]:
            group = self.connection.execute(
                """SELECT role FROM m_skill_target_cardrole_group
            WHERE group_id = ? LIMIT 1""",
                (basic["target_role_group_id"],),
            ).fetchall()
            target_type.fixed_roles = [x[0] for x in group]
        return target_type

    def lookup_batch_item_req_set(self, item_set_ids: Iterable[int]):
        id_list = ",".join(str(int(x)) for x in set(item_set_ids))

        rows = self.connection.execute(
            f"""
            SELECT m_training_tree_cell_item_set.id, content_type, content_id,
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
            """
            SELECT training_tree_cell_content_m_id, training_tree_design_m_id, training_tree_card_param_m_id
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

    def lookup_inline_image(self, iip):
        path = self.connection.execute(
            """SELECT path FROM m_inline_image WHERE id=?""", (iip,)
        ).fetchone()
        if path:
            return path[0]
        # ???
        path = self.connection.execute(
            """SELECT path FROM m_decoration_texture WHERE id=?""", (iip,)
        ).fetchone()
        if path:
            return path[0]

        return None
