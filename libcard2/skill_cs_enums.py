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

    AddAccessoryPassiveSkillRateBuff = 249
    AddAccessoryPassiveSkillRateDebuff = 250
    AddAccessoryPassiveSkillRateGimmickBuff = 251
    AddAccessoryPassiveSkillRateGimmickDebuff = 252
    AddActionSkillRateBase = 13
    AddActionSkillRateBaseBonus = 33
    AddActionSkillRateBaseBonusChangingHpRateMax = 35
    AddActionSkillRateBaseBonusChangingHpRateMin = 34
    AddActionSkillRateBuff = 22
    AddActionSkillRateBuffByNumOfGd = 164
    AddActionSkillRateBuffByNumOfSk = 163
    AddActionSkillRateBuffByNumOfSp = 162
    AddActionSkillRateBuffByNumOfVo = 161
    AddActionSkillRateDebuff = 76
    AddActionSkillRateDebuffByNumOfGd = 168
    AddActionSkillRateDebuffByNumOfSk = 167
    AddActionSkillRateDebuffByNumOfSp = 166
    AddActionSkillRateDebuffByNumOfVo = 165
    AddActionSkillRateGimmickBuff = 48
    AddActionSkillRateGimmickBuffByNumOfGd = 172
    AddActionSkillRateGimmickBuffByNumOfSk = 171
    AddActionSkillRateGimmickBuffByNumOfSp = 170
    AddActionSkillRateGimmickBuffByNumOfVo = 169
    AddActionSkillRateGimmickDebuff = 78
    AddActionSkillRateGimmickDebuffByNumOfGd = 176
    AddActionSkillRateGimmickDebuffByNumOfSk = 175
    AddActionSkillRateGimmickDebuffByNumOfSp = 174
    AddActionSkillRateGimmickDebuffByNumOfVo = 173
    AddActionSkillVoltageBaseBonus = 44
    AddActionSkillVoltageBuff = 24
    AddAdditionalPassiveSkillRateBuff = 243
    AddAdditionalPassiveSkillRateDebuff = 244
    AddAdditionalPassiveSkillRateGimmickBuff = 245
    AddAdditionalPassiveSkillRateGimmickDebuff = 246
    AddAppealBase = 10
    AddAppealBaseBonus = 26
    AddAppealBaseBonusChangingHpRateMax = 28
    AddAppealBaseBonusChangingHpRateMin = 27
    AddAppealBuff = 17
    AddAppealBuffByNumOfGd = 125
    AddAppealBuffByNumOfSk = 123
    AddAppealBuffByNumOfSp = 121
    AddAppealBuffByNumOfVo = 119
    AddAppealDebuff = 71
    AddAppealDebuffByNumOfGd = 126
    AddAppealDebuffByNumOfSk = 124
    AddAppealDebuffByNumOfSp = 122
    AddAppealDebuffByNumOfVo = 120
    AddAppealGimmickBuff = 49
    AddAppealGimmickBuffByNumOfGd = 143
    AddAppealGimmickBuffByNumOfSk = 141
    AddAppealGimmickBuffByNumOfSp = 139
    AddAppealGimmickBuffByNumOfVo = 137
    AddAppealGimmickDebuff = 81
    AddAppealGimmickDebuffByNumOfGd = 144
    AddAppealGimmickDebuffByNumOfSk = 142
    AddAppealGimmickDebuffByNumOfSp = 140
    AddAppealGimmickDebuffByNumOfVo = 138
    AddCollaboGauge = 3
    AddCollaboGaugeBase = 12
    AddCollaboGaugeBaseBonus = 29
    AddCollaboGaugeBaseBonusByComboCount = 30
    AddCollaboGaugeBaseBonusChangingHpRateMax = 32
    AddCollaboGaugeBaseBonusChangingHpRateMin = 31
    AddCollaboGaugeBuff = 19
    AddCollaboGaugeByAppeal = 92
    AddCollaboGaugeByMaxCollaboGauge = 91
    AddCollaboGaugeByStamina = 111
    AddCollaboGaugeByTechnique = 112
    AddCollaboGaugeDebuff = 73
    AddCollaboGaugeGimmickBuff = 45
    AddCollaboGaugeGimmickDebuff = 83
    AddCollaboVoltageBuff = 23
    AddCollaboVoltageBuffByAppeal = 25
    AddCollaboVoltageBuffByNumOfGd = 212
    AddCollaboVoltageBuffByNumOfSk = 211
    AddCollaboVoltageBuffByNumOfSp = 210
    AddCollaboVoltageBuffByNumOfVo = 209
    AddCollaboVoltageBuffByStamina = 107
    AddCollaboVoltageBuffByTechnique = 108
    AddCollaboVoltageDebuff = 77
    AddCollaboVoltageDebuffByNumOfGd = 216
    AddCollaboVoltageDebuffByNumOfSk = 215
    AddCollaboVoltageDebuffByNumOfSp = 214
    AddCollaboVoltageDebuffByNumOfVo = 213
    AddCollaboVoltageGimmickBuff = 50
    AddCollaboVoltageGimmickBuffByNumOfGd = 220
    AddCollaboVoltageGimmickBuffByNumOfSk = 219
    AddCollaboVoltageGimmickBuffByNumOfSp = 218
    AddCollaboVoltageGimmickBuffByNumOfVo = 217
    AddCollaboVoltageGimmickDebuffByNumOfGd = 224
    AddCollaboVoltageGimmickDebuffByNumOfSk = 223
    AddCollaboVoltageGimmickDebuffByNumOfSp = 222
    AddCollaboVoltageGimmickDebuffByNumOfVo = 221
    AddComboActual = 8
    AddCriticalAppealBase = 15
    AddCriticalAppealBaseBonus = 40
    AddCriticalAppealBaseBonusByComboCount = 43
    AddCriticalAppealBaseBonusChangingHpRateMax = 42
    AddCriticalAppealBaseBonusChangingHpRateMin = 41
    AddCriticalAppealBuff = 21
    AddCriticalAppealBuffByNumOfGd = 196
    AddCriticalAppealBuffByNumOfSk = 195
    AddCriticalAppealBuffByNumOfSp = 194
    AddCriticalAppealBuffByNumOfVo = 193
    AddCriticalAppealDebuff = 75
    AddCriticalAppealDebuffByNumOfGd = 200
    AddCriticalAppealDebuffByNumOfSk = 199
    AddCriticalAppealDebuffByNumOfSp = 198
    AddCriticalAppealDebuffByNumOfVo = 197
    AddCriticalAppealGimmickBuff = 47
    AddCriticalAppealGimmickBuffByNumOfGd = 204
    AddCriticalAppealGimmickBuffByNumOfSk = 203
    AddCriticalAppealGimmickBuffByNumOfSp = 202
    AddCriticalAppealGimmickBuffByNumOfVo = 201
    AddCriticalAppealGimmickDebuff = 80
    AddCriticalAppealGimmickDebuffByNumOfGd = 208
    AddCriticalAppealGimmickDebuffByNumOfSk = 207
    AddCriticalAppealGimmickDebuffByNumOfSp = 206
    AddCriticalAppealGimmickDebuffByNumOfVo = 205
    AddCriticalRateBase = 14
    AddCriticalRateBaseBonus = 36
    AddCriticalRateBaseBonusByComboCount = 39
    AddCriticalRateBaseBonusByHpRateMax = 38
    AddCriticalRateBaseBonusByHpRateMin = 37
    AddCriticalRateBuff = 20
    AddCriticalRateBuffByNumOfGd = 180
    AddCriticalRateBuffByNumOfSk = 179
    AddCriticalRateBuffByNumOfSp = 178
    AddCriticalRateBuffByNumOfVo = 177
    AddCriticalRateDebuff = 74
    AddCriticalRateDebuffByNumOfGd = 184
    AddCriticalRateDebuffByNumOfSk = 183
    AddCriticalRateDebuffByNumOfSp = 182
    AddCriticalRateDebuffByNumOfVo = 181
    AddCriticalRateGimmickBuff = 46
    AddCriticalRateGimmickBuffByNumOfGd = 188
    AddCriticalRateGimmickBuffByNumOfSk = 187
    AddCriticalRateGimmickBuffByNumOfSp = 186
    AddCriticalRateGimmickBuffByNumOfVo = 185
    AddCriticalRateGimmickDebuff = 82
    AddCriticalRateGimmickDebuffByNumOfGd = 192
    AddCriticalRateGimmickDebuffByNumOfSk = 191
    AddCriticalRateGimmickDebuffByNumOfSp = 190
    AddCriticalRateGimmickDebuffByNumOfVo = 189
    AddDamage = 68
    AddDamageByNumOfGd = 133
    AddDamageByNumOfSk = 131
    AddDamageByNumOfSp = 129
    AddDamageByNumOfVo = 127
    AddIndividualPassiveSkillRateBuff = 237
    AddIndividualPassiveSkillRateDebuff = 238
    AddIndividualPassiveSkillRateGimmickBuff = 239
    AddIndividualPassiveSkillRateGimmickDebuff = 240
    AddLastLeaveBuff = 106
    AddPassiveSkillRateBuff = 231
    AddPassiveSkillRateDebuff = 232
    AddPassiveSkillRateGimmickBuff = 233
    AddPassiveSkillRateGimmickDebuff = 234
    AddRoleMeritBuffBase = 16
    AddShield = 4
    AddShieldByCardAppeal = 113
    AddShieldByCardStamina = 94
    AddShieldByCardTechnique = 114
    AddShieldByComboCount = 95
    AddShieldByMaxLife = 93
    AddSquadChangeEffectCollaboBuff = 227
    AddSquadChangeEffectCollaboGimmickBuff = 230
    AddSquadChangeEffectHealBuff = 118
    AddSquadChangeEffectHealGimmickBuff = 136
    AddSquadChangeEffectRecastBuff = 226
    AddSquadChangeEffectRecastGimmickBuff = 229
    AddSquadChangeEffectVoltageBuff = 225
    AddSquadChangeEffectVoltageGimmickBuff = 228
    AddSquadDemeritDebuff = 117
    AddSquadDemeritGimmickDebuff = 135
    AddStaminaBase = 9
    AddStaminaDamageBaseBonus = 102
    AddStaminaDamageBaseBonusChangingHpRateMax = 104
    AddStaminaDamageBaseBonusChangingHpRateMin = 103
    AddTechniqueBase = 11
    AddVoltage = 2
    AddVoltageBuff = 18
    AddVoltageByAppeal = 90
    AddVoltageByStamina = 109
    AddVoltageByTechnique = 110
    AddVoltageDebuff = 72
    AddVoltageGimmickBuff = 51
    AddVoltageGimmickDebuff = 79
    HealLife = 5
    HealLifeByCardAppeal = 115
    HealLifeByCardAppealAndNumOfGd = 152
    HealLifeByCardAppealAndNumOfSk = 151
    HealLifeByCardAppealAndNumOfSp = 150
    HealLifeByCardAppealAndNumOfVo = 149
    HealLifeByCardStamina = 97
    HealLifeByCardStaminaAndNumOfGd = 148
    HealLifeByCardStaminaAndNumOfSk = 147
    HealLifeByCardStaminaAndNumOfSp = 146
    HealLifeByCardStaminaAndNumOfVo = 145
    HealLifeByCardTechnique = 116
    HealLifeByCardTechniqueAndNumOfGd = 156
    HealLifeByCardTechniqueAndNumOfSk = 155
    HealLifeByCardTechniqueAndNumOfSp = 154
    HealLifeByCardTechniqueAndNumOfVo = 153
    HealLifeByComboCount = 98
    HealLifeByMaxLife = 96
    HealLifeByMaxLifeAndNumOfGd = 160
    HealLifeByMaxLifeAndNumOfSk = 159
    HealLifeByMaxLifeAndNumOfSp = 158
    HealLifeByMaxLifeAndNumOfVo = 157
    HealLifeByNumOfGd = 134
    HealLifeByNumOfSk = 132
    HealLifeByNumOfSp = 130
    HealLifeByNumOfVo = 128
    Non = 1
    ReduceActionSkillRateBaseBonus = 86
    ReduceActionSkillVoltageBaseBonus = 89
    ReduceAppealBaseBonus = 84
    ReduceCollaboGaugeBaseBonus = 85
    ReduceCriticalAppealBaseBonus = 88
    ReduceCriticalRateBaseBonus = 87
    ReduceDamageActualBuff = 6
    ReduceStaminaDamageBaseBonus = 99
    RemoveAccessoryPassiveSkillRateBuff = 253
    RemoveAccessoryPassiveSkillRateDebuff = 254
    RemoveActionSkillRateBuff = 58
    RemoveActionSkillRateDebuff = 66
    RemoveAdditionalPassiveSkillRateBuff = 247
    RemoveAdditionalPassiveSkillRateDebuff = 248
    RemoveAllBuff = 52
    RemoveAllDebuff = 60
    RemoveAppealBuff = 53
    RemoveAppealDebuff = 61
    RemoveCollaboGauge = 69
    RemoveCollaboGaugeBuff = 55
    RemoveCollaboGaugeDebuff = 63
    RemoveCollaboVoltageBuff = 59
    RemoveCollaboVoltageDebuff = 67
    RemoveCriticalAppealBuff = 57
    RemoveCriticalAppealDebuff = 65
    RemoveCriticalRateBuff = 56
    RemoveCriticalRateDebuff = 64
    RemoveIndividualPassiveSkillRateBuff = 241
    RemoveIndividualPassiveSkillRateDebuff = 242
    RemovePassiveSkillRateBuff = 235
    RemovePassiveSkillRateDebuff = 236
    RemoveShield = 70
    RemoveVoltageBuff = 54
    RemoveVoltageDebuff = 62
    StaminaDamageBuffByComboCount = 7
    StaminaDamageDebuff = 101
    StaminaDamageGimmickBuff = 100
    StaminaDamageGimmickDebuff = 105


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
    ST.AddShieldByCardAppeal,
    ST.AddShieldByCardTechnique,
    ST.HealLifeByCardTechnique,
    ST.AddCollaboGaugeByTechnique,
    ST.HealLifeByMaxLife,
    ST.AddShieldByMaxLife,
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
    ST.AddCollaboGaugeByTechnique,
    ST.HealLifeByMaxLife,
    ST.AddShieldByMaxLife,
    ST.AddAppealDebuffByNumOfVo,
    ST.AddCriticalAppealDebuff,
    ST.RemoveCollaboGauge,
    ST.ReduceAppealBaseBonus,
    ST.ReduceCollaboGaugeBaseBonus,
    ST.AddAppealBuffByNumOfVo,
    ST.HealLifeByCardTechnique,
    ST.AddCollaboVoltageBuffByTechnique,
}

MIXED_VALUE_SKILL_TYPES = {ST.AddVoltageBuff, ST.AddAppealBuff}
