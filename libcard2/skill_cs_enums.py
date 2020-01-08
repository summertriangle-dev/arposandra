# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file needs to be kept up to date with game enums.
# The corresponding C# enum type is named in the docstring of each class.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class FT:
    """SkillEffectFinishTimingType"""

    Permanent = 1
    Turn = 2
    Immediate = 3
    WaveEnd = 4
    WaveSuccess = 5
    Voltage = 6
    SpExecuteCount = 7
    ChangeSquadCount = 8
    Non = 255


class TT:
    """LivePassiveSkillTrigger"""

    BeforeLive = 1
    LiveStart = 2
    WaveStart = 3
    WaveSuccess = 4
    WaveFail = 5
    OnChangeLife = 6
    OnDamage = 7
    OnGotVoltage = 8
    OnChangeSquad = 9
    OnCollaboSkill = 10
    Non = 255


class CT:
    """SkillEffectConditionType"""

    Probability = 1
    HpLessThanPercent = 2
    LimitCount = 3
    VoltageMoreThanValue = 4
    TriggerLessThanValue = 5
    Non = 255


class ST:
    """SkillEffectType"""

    AddActionSkillRateBase = 13
    AddActionSkillRateBaseBonus = 35
    AddActionSkillRateBaseBonusChangingHpRateMax = 37
    AddActionSkillRateBaseBonusChangingHpRateMin = 36
    AddActionSkillRateBuff = 22
    AddActionSkillRateDebuff = 78
    AddActionSkillRateGimmickBuff = 50
    AddActionSkillRateGimmickDebuff = 80
    AddActionSkillVoltageBaseBonus = 46
    AddActionSkillVoltageBuff = 24
    AddAppealBase = 10
    AddAppealBaseBonus = 28
    AddAppealBaseBonusChangingHpRateMax = 30
    AddAppealBaseBonusChangingHpRateMin = 29
    AddAppealBuff = 17
    AddAppealBuffByNumOfGd = 125
    AddAppealBuffByNumOfSk = 123
    AddAppealBuffByNumOfSp = 121
    AddAppealBuffByNumOfVo = 119
    AddAppealDebuff = 73
    AddAppealDebuffByNumOfGd = 126
    AddAppealDebuffByNumOfSk = 124
    AddAppealDebuffByNumOfSp = 122
    AddAppealDebuffByNumOfVo = 120
    AddAppealGimmickBuff = 51
    AddAppealGimmickBuffByNumOfGd = 143
    AddAppealGimmickBuffByNumOfSk = 141
    AddAppealGimmickBuffByNumOfSp = 139
    AddAppealGimmickBuffByNumOfVo = 137
    AddAppealGimmickDebuff = 83
    AddAppealGimmickDebuffByNumOfGd = 144
    AddAppealGimmickDebuffByNumOfSk = 142
    AddAppealGimmickDebuffByNumOfSp = 140
    AddAppealGimmickDebuffByNumOfVo = 138
    AddCollaboGauge = 3
    AddCollaboGaugeBase = 12
    AddCollaboGaugeBaseBonus = 31
    AddCollaboGaugeBaseBonusByComboCount = 32
    AddCollaboGaugeBaseBonusChangingHpRateMax = 34
    AddCollaboGaugeBaseBonusChangingHpRateMin = 33
    AddCollaboGaugeBuff = 19
    AddCollaboGaugeByAppeal = 97
    AddCollaboGaugeByMaxCollaboGauge = 95
    AddCollaboGaugeByStamina = 96
    AddCollaboGaugeByTechnique = 98
    AddCollaboGaugeDebuff = 75
    AddCollaboGaugeGimmickBuff = 47
    AddCollaboGaugeGimmickDebuff = 85
    AddCollaboVoltageBuff = 23
    AddCollaboVoltageBuffByAppeal = 26
    AddCollaboVoltageBuffByStamina = 25
    AddCollaboVoltageBuffByTechnique = 27
    AddCollaboVoltageDebuff = 79
    AddCollaboVoltageGimmickBuff = 52
    AddComboActual = 8
    AddCriticalAppealBase = 15
    AddCriticalAppealBaseBonus = 42
    AddCriticalAppealBaseBonusByComboCount = 45
    AddCriticalAppealBaseBonusChangingHpRateMax = 44
    AddCriticalAppealBaseBonusChangingHpRateMin = 43
    AddCriticalAppealBuff = 21
    AddCriticalAppealDebuff = 77
    AddCriticalAppealGimmickBuff = 49
    AddCriticalAppealGimmickDebuff = 82
    AddCriticalRateBase = 14
    AddCriticalRateBaseBonus = 38
    AddCriticalRateBaseBonusByComboCount = 41
    AddCriticalRateBaseBonusByHpRateMax = 40
    AddCriticalRateBaseBonusByHpRateMin = 39
    AddCriticalRateBuff = 20
    AddCriticalRateDebuff = 76
    AddCriticalRateGimmickBuff = 48
    AddCriticalRateGimmickDebuff = 84
    AddDamage = 70
    AddDamageByNumOfGd = 133
    AddDamageByNumOfSk = 131
    AddDamageByNumOfSp = 129
    AddDamageByNumOfVo = 127
    AddLastLeaveBuff = 116
    AddRoleMeritBuffBase = 16
    AddShield = 4
    AddShieldByCardAppeal = 101
    AddShieldByCardStamina = 100
    AddShieldByCardTechnique = 102
    AddShieldByComboCount = 103
    AddShieldByMaxLife = 99
    AddSquadChangeEffectHealBuff = 118
    AddSquadChangeEffectHealGimmickBuff = 136
    AddSquadDemeritDebuff = 117
    AddSquadDemeritGimmickDebuff = 135
    AddStaminaBase = 9
    AddStaminaDamageBaseBonus = 112
    AddStaminaDamageBaseBonusChangingHpRateMax = 114
    AddStaminaDamageBaseBonusChangingHpRateMin = 113
    AddTechniqueBase = 11
    AddVoltage = 2
    AddVoltageBuff = 18
    AddVoltageByAppeal = 93
    AddVoltageByStamina = 92
    AddVoltageByTechnique = 94
    AddVoltageDebuff = 74
    AddVoltageGimmickBuff = 53
    AddVoltageGimmickDebuff = 81
    HealLife = 5
    HealLifeByCardAppeal = 106
    HealLifeByCardAppealAndNumOfGd = 152
    HealLifeByCardAppealAndNumOfSk = 151
    HealLifeByCardAppealAndNumOfSp = 150
    HealLifeByCardAppealAndNumOfVo = 149
    HealLifeByCardStamina = 105
    HealLifeByCardStaminaAndNumOfGd = 148
    HealLifeByCardStaminaAndNumOfSk = 147
    HealLifeByCardStaminaAndNumOfSp = 146
    HealLifeByCardStaminaAndNumOfVo = 145
    HealLifeByCardTechnique = 107
    HealLifeByCardTechniqueAndNumOfGd = 156
    HealLifeByCardTechniqueAndNumOfSk = 155
    HealLifeByCardTechniqueAndNumOfSp = 154
    HealLifeByCardTechniqueAndNumOfVo = 153
    HealLifeByComboCount = 108
    HealLifeByMaxLife = 104
    HealLifeByMaxLifeAndNumOfGd = 160
    HealLifeByMaxLifeAndNumOfSk = 159
    HealLifeByMaxLifeAndNumOfSp = 158
    HealLifeByMaxLifeAndNumOfVo = 157
    HealLifeByNumOfGd = 134
    HealLifeByNumOfSk = 132
    HealLifeByNumOfSp = 130
    HealLifeByNumOfVo = 128
    Non = 1
    ReduceActionSkillRateBaseBonus = 88
    ReduceActionSkillVoltageBaseBonus = 91
    ReduceAppealBaseBonus = 86
    ReduceCollaboGaugeBaseBonus = 87
    ReduceCriticalAppealBaseBonus = 90
    ReduceCriticalRateBaseBonus = 89
    ReduceDamageActualBuff = 6
    ReduceStaminaDamageBaseBonus = 109
    RemoveActionSkillRateBuff = 60
    RemoveActionSkillRateDebuff = 68
    RemoveAllBuff = 54
    RemoveAllDebuff = 62
    RemoveAppealBuff = 55
    RemoveAppealDebuff = 63
    RemoveCollaboGauge = 71
    RemoveCollaboGaugeBuff = 57
    RemoveCollaboGaugeDebuff = 65
    RemoveCollaboVoltageBuff = 61
    RemoveCollaboVoltageDebuff = 69
    RemoveCriticalAppealBuff = 59
    RemoveCriticalAppealDebuff = 67
    RemoveCriticalRateBuff = 58
    RemoveCriticalRateDebuff = 66
    RemoveShield = 72
    RemoveVoltageBuff = 56
    RemoveVoltageDebuff = 64
    StaminaDamageBuffByComboCount = 7
    StaminaDamageDebuff = 111
    StaminaDamageGimmickBuff = 110
    StaminaDamageGimmickDebuff = 115


# ~~~~~~~~~~~~~~~~~~~~~~~~~
# End of C# constant data.
# ~~~~~~~~~~~~~~~~~~~~~~~~~

IMPLICIT_TARGET_SKILL_TYPES = {
    ST.ReduceDamageActualBuff,
    ST.AddShieldByComboCount,
    ST.HealLifeByCardStamina,
    ST.AddCollaboGaugeByAppeal,
    ST.AddVoltageByAppeal,
    ST.AddCollaboGaugeByMaxCollaboGauge,
    ST.AddShieldByCardStamina,
    ST.AddCollaboGauge,
    ST.AddCollaboVoltageBuffByAppeal,
    ST.AddCollaboVoltageBuff,
    ST.HealLife,
    ST.AddStaminaDamageBaseBonusChangingHpRateMax,
    ST.HealLifeByComboCount,
    ST.AddComboActual,
    ST.AddShield,
    ST.AddLastLeaveBuff,
    ST.AddVoltage,
}

PERCENT_VALUE_SKILL_TYPES = {
    ST.AddCollaboGaugeDebuff,
    ST.AddCriticalAppealBaseBonus,
    ST.AddCollaboGaugeBuff,
    ST.AddCriticalAppealBase,
    ST.ReduceActionSkillRateBaseBonus,
    ST.AddLastLeaveBuff,
    ST.AddCriticalAppealBuff,
    ST.AddShieldByCardStamina,
    ST.AddAppealBaseBonusChangingHpRateMax,
    ST.AddRoleMeritBuffBase,
    ST.AddStaminaBase,
    ST.AddAppealBaseBonus,
    ST.AddActionSkillRateBaseBonus,
    ST.AddVoltageByAppeal,
    ST.AddStaminaDamageBaseBonusChangingHpRateMax,
    ST.AddAppealBase,
    ST.ReduceDamageActualBuff,
    ST.AddCollaboGaugeByAppeal,
    ST.HealLifeByCardStamina,
    ST.AddCollaboGaugeBaseBonus,
    ST.AddCollaboVoltageBuffByAppeal,
    ST.AddCriticalRateBuff,
    ST.AddActionSkillRateBuff,
    ST.AddCriticalAppealBaseBonusByComboCount,
    ST.AddActionSkillRateBase,
    ST.AddTechniqueBase,
    ST.AddCollaboGaugeBaseBonusChangingHpRateMax,
    ST.AddAppealDebuff,
    ST.AddCollaboGaugeByMaxCollaboGauge,
    ST.AddActionSkillRateBaseBonusChangingHpRateMax,
    ST.AddActionSkillRateDebuff,
    ST.AddShieldByCardAppeal,
    ST.AddShieldByCardTechnique,
    ST.AddSquadChangeEffectHealBuff,
}

MIXED_VALUE_SKILL_TYPES = {ST.AddVoltageBuff, ST.AddAppealBuff}
