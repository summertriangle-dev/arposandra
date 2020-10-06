import sys
import os

from libcard2 import skill_cs_enums, string_mgr, master

SKILL_ID_REVERSE_MAP = {
    v: k for k, v in skill_cs_enums.ST.__dict__.items() if k[0].upper() == k[0] and k[0].isalpha()
}


def format_skill_example(da, name, descr, tag):
    sl = da.lookup_strings({name, descr})
    return f"# {tag}/{sl.get(name, name)}: {sl.get(descr, descr)}"


def find_skill_type_example(mdb, da, seid):
    cur = mdb.connection.cursor()
    answer = cur.execute(
        """
        SELECT
        m_live_difficulty_gimmick.name,
        m_live_difficulty_gimmick.description
        FROM m_live_difficulty_gimmick
        LEFT JOIN m_skill ON (m_live_difficulty_gimmick.skill_master_id == m_skill.id)
        LEFT JOIN m_skill_effect ON (m_skill.skill_effect_master_id1 == m_skill_effect.id)
        WHERE m_skill_effect.effect_type = ?
        """,
        (seid,),
    ).fetchone()
    if answer:
        return format_skill_example(da, answer[0], answer[1], "PersistentGimmick")

    answer = cur.execute(
        """
        SELECT m_live_difficulty_note_gimmick.name,
            m_live_difficulty_note_gimmick.description FROM m_live_difficulty_note_gimmick
        LEFT JOIN m_skill ON (m_live_difficulty_note_gimmick.skill_master_id == m_skill.id)
        LEFT JOIN m_skill_effect ON (m_skill.skill_effect_master_id1 == m_skill_effect.id)
        WHERE m_skill_effect.effect_type = ?
        """,
        (seid,),
    ).fetchone()
    if answer:
        return format_skill_example(da, answer[0], answer[1], "NoteGimmick")

    answer = cur.execute(
        """
        SELECT name, description FROM m_passive_skill
        LEFT JOIN m_skill ON (m_passive_skill.skill_master_id == m_skill.id)
        LEFT JOIN m_skill_effect ON (m_skill.skill_effect_master_id1 == m_skill_effect.id)
        WHERE m_skill_effect.effect_type = ?
        """,
        (seid,),
    ).fetchone()
    if answer:
        return format_skill_example(da, answer[0], answer[1], "PassiveSkill")

    answer = cur.execute(
        """
        SELECT name, description FROM m_accessory_passive_skill
        LEFT JOIN m_accessory_passive_skill_level ON
            (m_accessory_passive_skill_level.accessory_passive_skill_master_id
                == m_accessory_passive_skill.id)
        LEFT JOIN m_skill ON (m_accessory_passive_skill.skill_master_id == m_skill.id)
        LEFT JOIN m_skill_effect ON (m_skill.skill_effect_master_id1 == m_skill_effect.id)
        WHERE m_skill_effect.effect_type = ?
        """,
        (seid,),
    ).fetchone()
    if answer:
        return format_skill_example(da, answer[0], answer[1], "AccessoryPassiveSkill")

    answer = cur.execute(
        """
        SELECT m_active_skill.name, m_active_skill.description
        FROM m_active_skill
        LEFT JOIN m_skill ON (m_active_skill.skill_master_id == m_skill.id)
        LEFT JOIN m_skill_effect ON (m_skill.skill_effect_master_id1 == m_skill_effect.id)
        WHERE m_skill_effect.effect_type = ?
        """,
        (seid,),
    ).fetchone()
    if answer:
        return format_skill_example(da, answer[0], answer[1], "ActiveSkill")


def audit(lang, mdb, da):
    target = __import__(f"libcard2.localization.skills_{lang}", fromlist=[lang.upper()])
    target = getattr(target, lang.upper())

    nactual = len(SKILL_ID_REVERSE_MAP)
    ncovered = 0
    for sid, symbol in SKILL_ID_REVERSE_MAP.items():
        if sid not in target.skill_effect.data:
            have_example = find_skill_type_example(mdb, da, sid)
            if have_example:
                print(f"# Missing: ST.{symbol}")
                print(have_example)
        else:
            ncovered += 1
    print(f"# {ncovered} skills described. {nactual - ncovered} missing.")


def main():
    master_db = master.MasterData(os.getenv("ASTOOL_MASTER"))
    da = string_mgr.DictionaryAccess(os.getenv("ASTOOL_MASTER"), "ja")

    langs = [l.lower() for l in sys.argv[1:]]
    for lang in langs:
        print(f"# ------- AUDIT for {lang} --------------------------------------")
        audit(lang, master_db, da)
        print()


if __name__ == "__main__":
    main()
