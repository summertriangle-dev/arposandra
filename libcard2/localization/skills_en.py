from ..dataclasses import Card
from ..skill_description_base import SkillEffectDescriberContext, AnySkill
from ..skill_cs_enums import ST, TT, CT, FT

EN = SkillEffectDescriberContext()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Routines for English-language skill target descriptions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def _ordinal(n):
    SUFFIXES = {1: "st", 2: "nd", 3: "rd"}
    if 1 <= (n % 10) <= 3 and n // 10 != 1:
        suff = SUFFIXES[n % 10]
    else:
        suff = "th"
    return f"{n}{suff}"


def _divint(value):
    vf = value / 100
    vi = value // 100
    if vf == vi:
        return f"{vi}%"
    else:
        return f"{vf}%"


def _times(value):
    if value == 1:
        return "once"
    else:
        return f"{value} times"


@EN.target_clause
def _(tt: AnySkill, base, context: Card = None):
    if tt.self_only:
        return "Applies to: Just this card"

    complex_ = ["Applies to:"]
    if tt.owner_party:
        complex_.append("This card's party")
    elif tt.owner_school:
        if context:
            synthetic = f"kars.group_{context.member.group}"
            complex_.append(f"{base.lookup_single_string(synthetic)} members")
        else:
            complex_.append("Same idol group")
    elif tt.owner_year:
        if context:
            complex_.append(f"{_ordinal(context.member.year)} years")
        else:
            complex_.append("Same school year")
    elif tt.owner_subunit:
        if context:
            synthetic = f"kars.subunit_{context.member.subunit}"
            complex_.append(f"{base.lookup_single_string(synthetic)} members")
        else:
            complex_.append("Same subunit")
    elif tt.owner_attribute:
        if context:
            synthetic = f"kars.attribute_{context.attribute}"
            complex_.append(f"{base.lookup_single_string(synthetic)} cards")
        else:
            complex_.append("Same card attribute")
    elif tt.owner_role:
        if context:
            synthetic = f"kars.role_{context.role}"
            complex_.append(f"{base.lookup_single_string(synthetic)} cards")
        else:
            complex_.append("Same card role")
    elif tt.fixed_attributes:
        c = ", ".join(base.lookup_single_string(f"kars.attribute_{a}") for a in tt.fixed_attributes)
        complex_.append(f"{c} cards")
    elif tt.fixed_roles:
        c = ", ".join(base.lookup_single_string(f"kars.role_{a}") for a in tt.fixed_roles)
        complex_.append(f"{c} cards")
    elif tt.fixed_schools:
        c = ", ".join(base.lookup_single_string(f"kars.group_{a}") for a in tt.fixed_schools)
        complex_.append(f"{c} members")
    elif tt.fixed_subunits:
        c = ", ".join(base.lookup_single_string(f"kars.subunit_{a}") for a in tt.fixed_subunits)
        complex_.append(f"{c} members")
    elif tt.fixed_years:
        c = ", ".join(_ordinal(y) for y in tt.fixed_years)
        complex_.append(f"{c} years")
    elif tt.fixed_members:
        c = ", ".join(
            base.lookup_single_string(f"k.m_dic_member_name_romaji_{a}") for a in tt.fixed_members
        )
        complex_.append(c)
    else:
        complex_.append("Everyone")

    if tt.not_self:
        if (tt.owner_party and tt.apply_type >= 2) or tt.apply_count >= 8:
            complex_.append("(except this card)")
        else:
            complex_.append(f"({tt.apply_count} cards, except this one)")
    return " ".join(complex_)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Routines for English-language skill descriptions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@EN.birdseye_clause
def _(effect1, effect2):
    m = SkillEffectDescriberContext.mod_value
    return f"{m(effect1)}..{m(effect2)}"


@EN.finish_clause
def _(skill, tags):
    finish_type, finish_value = skill.levels[0][8], skill.levels[0][9]
    if finish_type == FT.Turn:
        return f" for {tags['let']}{finish_value}{tags['end']} notes"
    if finish_type == FT.SpExecuteCount:
        if finish_value == 1:
            return " on the next SP burst"
        else:
            return f" for the next {tags['let']}{finish_value}{tags['end']} SP bursts"
    if finish_type == FT.ChangeSquadCount:
        if finish_value == 1:
            return " until the next party switch"
        else:
            return f" for the next {tags['let']}{finish_value}{tags['end']} party changes"
    return ""


@EN.trigger_clause
def _(skill, tags):
    if skill.has_complex_trigger():
        phrases = []
        if skill.trigger_probability != 10000:
            phrases.append(f"{tags['let']}{_divint(skill.trigger_probability)}{tags['end']} chance")
        if skill.trigger_type == TT.LiveStart:
            phrases.append("when live starts")
        elif skill.trigger_type == TT.WaveStart:
            phrases.append("when appeal starts")
        elif skill.trigger_type == TT.WaveSuccess:
            phrases.append("after passing an appeal")
        elif skill.trigger_type == TT.WaveFail:
            phrases.append("after failing an appeal")
        elif skill.trigger_type in {TT.OnChangeLife, TT.OnDamage}:
            phrases.append("when taking damage")
        elif skill.trigger_type == TT.OnGotVoltage:
            phrases.append("when gaining voltage")
        elif skill.trigger_type == TT.OnChangeSquad:
            phrases.append("on party rotation")
        elif skill.trigger_type == TT.OnCollaboSkill:
            phrases.append("on SP burst")
        elif skill.trigger_type == TT.Non or skill.trigger_type == TT.BeforeLive:
            pass
        else:
            phrases.append(f"when an undocumented event ({skill.trigger_type}) occurs")

        if skill.condition_type == CT.HpLessThanPercent:
            phrases.append(
                f"(if stamina below {tags['let']}{_divint(skill.condition_value)}{tags['end']})"
            )
        elif skill.condition_type == CT.LimitCount:
            phrases.append(
                f"(only {tags['let']}{_times(skill.condition_value)}{tags['end']} per live)"
            )
        elif skill.condition_type == CT.VoltageMoreThanValue:
            phrases.append(
                f"(if voltage is over {tags['let']}{skill.condition_value}{tags['end']})"
            )
        elif skill.condition_type == CT.TriggerLessThanValue:
            phrases.append(
                f"(if SP gauge below {tags['let']}{_divint(skill.condition_value)}{tags['end']} full)"
            )
        elif skill.condition_type == CT.Non:
            pass
        else:
            phrases.append(
                f"(undocumented condition {skill.condition_type}, {skill.condition_value})"
            )

        a = " ".join(phrases)
        if a:
            return a[0].upper() + a[1:] + ": "
        return ""
    else:
        return f"{tags['let']}{_divint(skill.trigger_probability)}{tags['end']} chance: "


# fmt: off

EN.skill_effect[ST.AddActionSkillRateBase] = \
    "Base skill activation rate up by {var}{value}{end}"
EN.skill_effect[ST.AddActionSkillRateBaseBonus] = \
    "Increase base skill activation rate by {var}{value}{end}"
EN.skill_effect[ST.AddActionSkillRateBaseBonusChangingHpRateMax] = \
    "Base skill activation rate up based on current stamina (max. {var}{value}{end})"
EN.skill_effect[ST.AddActionSkillRateBuff] = \
    "Buff. Increase skill activation rate by {var}{value}{end}"
EN.skill_effect[ST.AddActionSkillRateDebuff] = \
    "Debuff. Decrease skill activation rate by {var}{value}{end}"
EN.skill_effect[ST.AddAppealBase] = \
    "Base appeal up by {var}{value}{end}"
EN.skill_effect[ST.AddAppealBaseBonus] = \
    "Increase base appeal by {var}{value}{end}"
EN.skill_effect[ST.AddAppealBaseBonusChangingHpRateMax] = \
    "Base appeal up based on current stamina (max. {var}{value}{end})"
EN.skill_effect[ST.AddAppealBuff] = \
    "Buff. Increase effective appeal by {var}{value}{end}"
EN.skill_effect[ST.AddAppealDebuff] = \
    "Debuff. Appeal down by {var}{value}{end}"
EN.skill_effect[ST.AddCollaboGauge] = \
    "Add {var}{value}{end} to SP gauge"
EN.skill_effect[ST.AddCollaboGaugeBaseBonus] = \
    "Increase base SP gain by {var}{value}{end}"
EN.skill_effect[ST.AddCollaboGaugeBaseBonusChangingHpRateMax] = \
    "Base SP gain up based on current stamina (max. {var}{value}{end})"
EN.skill_effect[ST.AddCollaboGaugeBuff] = \
    "Buff. Increase SP gauge fill rate by {var}{value}{end}"
EN.skill_effect[ST.AddCollaboGaugeByAppeal] = \
    "Fill SP gauge by {var}{value}{end} of this card's appeal"
EN.skill_effect[ST.AddCollaboGaugeByMaxCollaboGauge] = \
    "Fill SP gauge by {var}{value}{end}"
EN.skill_effect[ST.AddCollaboGaugeDebuff] = \
    "Debuff. Decrease SP gauge fill rate by {var}{value}{end}"
EN.skill_effect[ST.AddCollaboVoltageBuff] = \
    "Buff. Increase voltage gain from SP burst by {var}{value}{end}"
EN.skill_effect[ST.AddCollaboVoltageBuffByAppeal] = \
    "Buff. Increase voltage gain from SP burst by {var}{value}{end} of this card's appeal"
EN.skill_effect[ST.AddComboActual] = \
    "Add {var}{value}{end} combo"
EN.skill_effect[ST.AddCriticalAppealBase] = \
    "Base voltage from critical notes up by {var}{value}{end}"
EN.skill_effect[ST.AddCriticalAppealBaseBonus] = \
    "Increase voltage gain from critical notes by {var}{value}{end}"
EN.skill_effect[ST.AddCriticalAppealBaseBonusByComboCount] = \
    "Base voltage gain from critical notes up based on current combo (max. {var}{value}{end} at 150 combo)"
EN.skill_effect[ST.AddCriticalAppealBuff] = \
    "Buff. Increase voltage gain for critical notes by {var}{value}{end}"
EN.skill_effect[ST.AddCriticalRateBuff] = \
    "Buff. Increase critical rate by {var}{value}{end}"
EN.skill_effect[ST.AddDamage] = \
    "Take {var}{value}{end} damage"
EN.skill_effect[ST.AddLastLeaveBuff] = \
    "Buff. If stamina would drop to zero, restore {var}{value}{end} and continue the live"
EN.skill_effect[ST.AddRoleMeritBuffBase] = \
    "Buff. Increase base effect of this card's role by {var}{value}{end}"
EN.skill_effect[ST.AddShield] = \
    "Add {var}{value}{end} shield points"
EN.skill_effect[ST.AddShieldByCardAppeal] = \
    "Add {var}{value}{end} of this card's appeal to shield points"
EN.skill_effect[ST.AddShieldByCardStamina] = \
    "Add {var}{value}{end} of this card's stamina to shield points"
EN.skill_effect[ST.AddShieldByCardTechnique] = \
    "Add {var}{value}{end} of this card's technique to shield points"
EN.skill_effect[ST.AddShieldByComboCount] = \
    "Add shield points based on current combo (max. {var}{value}{end} at 150 combo)"
EN.skill_effect[ST.AddSquadChangeEffectHealBuff] = \
    "Increase the stamina restored by Guard-type cards' rotation effect by {var}{value}{end}"
EN.skill_effect[ST.AddStaminaBase] = \
    "Base stamina up by {var}{value}{end}"
EN.skill_effect[ST.AddStaminaDamageBaseBonusChangingHpRateMax] = \
    "Reduce damage based on current stamina (max. {var}{value}{end})"
EN.skill_effect[ST.AddTechniqueBase] = \
    "Base technique up by {var}{value}{end}"
EN.skill_effect[ST.AddVoltage] = \
    "Add {var}{value}{end} voltage"
EN.skill_effect[ST.AddVoltageBuff] = \
    "Buff. Increase voltage gain by {var}{value}{end}"
EN.skill_effect[ST.AddVoltageByAppeal] = \
    "Add {var}{value}{end} of this card's appeal to voltage"
EN.skill_effect[ST.HealLife] = \
    "Restore {var}{value}{end} stamina"
EN.skill_effect[ST.HealLifeByCardStamina] = \
    "Restore {var}{value}{end} of this card's stamina"
EN.skill_effect[ST.HealLifeByComboCount] = \
    "Restore stamina based on current combo (max. {var}{value}{end} at 150 combo)"
EN.skill_effect[ST.HealLifeByNumOfGd] = \
    "Restore {var}{value}{end} stamina for each Guard-type card on the team"
EN.skill_effect[ST.ReduceActionSkillRateBaseBonus] = \
    "Base skill activation rate down by {var}{value}{end}"
EN.skill_effect[ST.ReduceDamageActualBuff] = \
    "Buff. Reduce stamina drain by {var}{value}{end}"
EN.skill_effect[ST.AddCollaboGaugeByTechnique] = \
    "Add {var}{value}{end} of this card's technique to SP gauge"
EN.skill_effect[ST.RemoveAllBuff] = \
    "Remove all active buffs"
EN.skill_effect[ST.RemoveAllDebuff] = \
    "Remove all debuffs"

# fmt: on
