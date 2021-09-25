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
    OnAppealCritical = 11
    OnNoteScore = 12
    Non = 255


class CT:
    """SkillEffectConditionType"""

    Probability = 1
    HpLessThanPercent = 2
    LimitCount = 3
    VoltageMoreThanValue = 4
    TriggerLessThanValue = 5
    OnlyOwner = 6
    AttributeMatch = 7
    Non = 255


class ST:
    """SkillEffectType"""

    Non = 1
    AddVoltage = 2
    AddCollaboGauge = 3
    AddShield = 4
    HealLife = 5
    ReduceDamageActualBuff = 6
    StaminaDamageBuffByComboCount = 7
    AddComboActual = 8
    AddStaminaBase = 9
    AddAppealBase = 10
    AddTechniqueBase = 11
    AddCollaboGaugeBase = 12
    AddActionSkillRateBase = 13
    AddCriticalRateBase = 14
    AddCriticalAppealBase = 15
    AddRoleMeritBuffBase = 16
    AddAppealBuff = 17
    AddVoltageBuff = 18
    AddCollaboGaugeBuff = 19
    AddCriticalRateBuff = 20
    AddCriticalAppealBuff = 21
    AddActionSkillRateBuff = 22
    AddCollaboVoltageBuff = 23
    AddActionSkillVoltageBuff = 24
    AddCollaboVoltageBuffByAppeal = 25
    AddAppealBaseBonus = 26
    AddAppealBaseBonusChangingHpRateMin = 27
    AddAppealBaseBonusChangingHpRateMax = 28
    AddCollaboGaugeBaseBonus = 29
    AddCollaboGaugeBaseBonusByComboCount = 30
    AddCollaboGaugeBaseBonusChangingHpRateMin = 31
    AddCollaboGaugeBaseBonusChangingHpRateMax = 32
    AddActionSkillRateBaseBonus = 33
    AddActionSkillRateBaseBonusChangingHpRateMin = 34
    AddActionSkillRateBaseBonusChangingHpRateMax = 35
    AddCriticalRateBaseBonus = 36
    AddCriticalRateBaseBonusByHpRateMin = 37
    AddCriticalRateBaseBonusByHpRateMax = 38
    AddCriticalRateBaseBonusByComboCount = 39
    AddCriticalAppealBaseBonus = 40
    AddCriticalAppealBaseBonusChangingHpRateMin = 41
    AddCriticalAppealBaseBonusChangingHpRateMax = 42
    AddCriticalAppealBaseBonusByComboCount = 43
    AddActionSkillVoltageBaseBonus = 44
    AddCollaboGaugeGimmickBuff = 45
    AddCriticalRateGimmickBuff = 46
    AddCriticalAppealGimmickBuff = 47
    AddActionSkillRateGimmickBuff = 48
    AddAppealGimmickBuff = 49
    AddCollaboVoltageGimmickBuff = 50
    AddVoltageGimmickBuff = 51
    RemoveAllBuff = 52
    RemoveAppealBuff = 53
    RemoveVoltageBuff = 54
    RemoveCollaboGaugeBuff = 55
    RemoveCriticalRateBuff = 56
    RemoveCriticalAppealBuff = 57
    RemoveActionSkillRateBuff = 58
    RemoveCollaboVoltageBuff = 59
    RemoveAllDebuff = 60
    RemoveAppealDebuff = 61
    RemoveVoltageDebuff = 62
    RemoveCollaboGaugeDebuff = 63
    RemoveCriticalRateDebuff = 64
    RemoveCriticalAppealDebuff = 65
    RemoveActionSkillRateDebuff = 66
    RemoveCollaboVoltageDebuff = 67
    AddDamage = 68
    RemoveCollaboGauge = 69
    RemoveShield = 70
    AddAppealDebuff = 71
    AddVoltageDebuff = 72
    AddCollaboGaugeDebuff = 73
    AddCriticalRateDebuff = 74
    AddCriticalAppealDebuff = 75
    AddActionSkillRateDebuff = 76
    AddCollaboVoltageDebuff = 77
    AddActionSkillRateGimmickDebuff = 78
    AddVoltageGimmickDebuff = 79
    AddCriticalAppealGimmickDebuff = 80
    AddAppealGimmickDebuff = 81
    AddCriticalRateGimmickDebuff = 82
    AddCollaboGaugeGimmickDebuff = 83
    ReduceAppealBaseBonus = 84
    ReduceCollaboGaugeBaseBonus = 85
    ReduceActionSkillRateBaseBonus = 86
    ReduceCriticalRateBaseBonus = 87
    ReduceCriticalAppealBaseBonus = 88
    ReduceActionSkillVoltageBaseBonus = 89
    AddVoltageByAppeal = 90
    AddCollaboGaugeByMaxCollaboGauge = 91
    AddCollaboGaugeByAppeal = 92
    AddShieldByMaxLife = 93
    AddShieldByCardStamina = 94
    AddShieldByComboCount = 95
    HealLifeByMaxLife = 96
    HealLifeByCardStamina = 97
    HealLifeByComboCount = 98
    ReduceStaminaDamageBaseBonus = 99
    StaminaDamageGimmickBuff = 100
    StaminaDamageDebuff = 101
    AddStaminaDamageBaseBonus = 102
    AddStaminaDamageBaseBonusChangingHpRateMin = 103
    AddStaminaDamageBaseBonusChangingHpRateMax = 104
    StaminaDamageGimmickDebuff = 105
    AddLastLeaveBuff = 106
    AddCollaboVoltageBuffByStamina = 107
    AddCollaboVoltageBuffByTechnique = 108
    AddVoltageByStamina = 109
    AddVoltageByTechnique = 110
    AddCollaboGaugeByStamina = 111
    AddCollaboGaugeByTechnique = 112
    AddShieldByCardAppeal = 113
    AddShieldByCardTechnique = 114
    HealLifeByCardAppeal = 115
    HealLifeByCardTechnique = 116
    AddSquadDemeritDebuff = 117
    AddSquadChangeEffectHealBuff = 118
    AddAppealBuffByNumOfVo = 119
    AddAppealDebuffByNumOfVo = 120
    AddAppealBuffByNumOfSp = 121
    AddAppealDebuffByNumOfSp = 122
    AddAppealBuffByNumOfSk = 123
    AddAppealDebuffByNumOfSk = 124
    AddAppealBuffByNumOfGd = 125
    AddAppealDebuffByNumOfGd = 126
    AddDamageByNumOfVo = 127
    HealLifeByNumOfVo = 128
    AddDamageByNumOfSp = 129
    HealLifeByNumOfSp = 130
    AddDamageByNumOfSk = 131
    HealLifeByNumOfSk = 132
    AddDamageByNumOfGd = 133
    HealLifeByNumOfGd = 134
    AddSquadDemeritGimmickDebuff = 135
    AddSquadChangeEffectHealGimmickBuff = 136
    AddAppealGimmickBuffByNumOfVo = 137
    AddAppealGimmickDebuffByNumOfVo = 138
    AddAppealGimmickBuffByNumOfSp = 139
    AddAppealGimmickDebuffByNumOfSp = 140
    AddAppealGimmickBuffByNumOfSk = 141
    AddAppealGimmickDebuffByNumOfSk = 142
    AddAppealGimmickBuffByNumOfGd = 143
    AddAppealGimmickDebuffByNumOfGd = 144
    HealLifeByCardStaminaAndNumOfVo = 145
    HealLifeByCardStaminaAndNumOfSp = 146
    HealLifeByCardStaminaAndNumOfSk = 147
    HealLifeByCardStaminaAndNumOfGd = 148
    HealLifeByCardAppealAndNumOfVo = 149
    HealLifeByCardAppealAndNumOfSp = 150
    HealLifeByCardAppealAndNumOfSk = 151
    HealLifeByCardAppealAndNumOfGd = 152
    HealLifeByCardTechniqueAndNumOfVo = 153
    HealLifeByCardTechniqueAndNumOfSp = 154
    HealLifeByCardTechniqueAndNumOfSk = 155
    HealLifeByCardTechniqueAndNumOfGd = 156
    HealLifeByMaxLifeAndNumOfVo = 157
    HealLifeByMaxLifeAndNumOfSp = 158
    HealLifeByMaxLifeAndNumOfSk = 159
    HealLifeByMaxLifeAndNumOfGd = 160
    AddActionSkillRateBuffByNumOfVo = 161
    AddActionSkillRateBuffByNumOfSp = 162
    AddActionSkillRateBuffByNumOfSk = 163
    AddActionSkillRateBuffByNumOfGd = 164
    AddActionSkillRateDebuffByNumOfVo = 165
    AddActionSkillRateDebuffByNumOfSp = 166
    AddActionSkillRateDebuffByNumOfSk = 167
    AddActionSkillRateDebuffByNumOfGd = 168
    AddActionSkillRateGimmickBuffByNumOfVo = 169
    AddActionSkillRateGimmickBuffByNumOfSp = 170
    AddActionSkillRateGimmickBuffByNumOfSk = 171
    AddActionSkillRateGimmickBuffByNumOfGd = 172
    AddActionSkillRateGimmickDebuffByNumOfVo = 173
    AddActionSkillRateGimmickDebuffByNumOfSp = 174
    AddActionSkillRateGimmickDebuffByNumOfSk = 175
    AddActionSkillRateGimmickDebuffByNumOfGd = 176
    AddCriticalRateBuffByNumOfVo = 177
    AddCriticalRateBuffByNumOfSp = 178
    AddCriticalRateBuffByNumOfSk = 179
    AddCriticalRateBuffByNumOfGd = 180
    AddCriticalRateDebuffByNumOfVo = 181
    AddCriticalRateDebuffByNumOfSp = 182
    AddCriticalRateDebuffByNumOfSk = 183
    AddCriticalRateDebuffByNumOfGd = 184
    AddCriticalRateGimmickBuffByNumOfVo = 185
    AddCriticalRateGimmickBuffByNumOfSp = 186
    AddCriticalRateGimmickBuffByNumOfSk = 187
    AddCriticalRateGimmickBuffByNumOfGd = 188
    AddCriticalRateGimmickDebuffByNumOfVo = 189
    AddCriticalRateGimmickDebuffByNumOfSp = 190
    AddCriticalRateGimmickDebuffByNumOfSk = 191
    AddCriticalRateGimmickDebuffByNumOfGd = 192
    AddCriticalAppealBuffByNumOfVo = 193
    AddCriticalAppealBuffByNumOfSp = 194
    AddCriticalAppealBuffByNumOfSk = 195
    AddCriticalAppealBuffByNumOfGd = 196
    AddCriticalAppealDebuffByNumOfVo = 197
    AddCriticalAppealDebuffByNumOfSp = 198
    AddCriticalAppealDebuffByNumOfSk = 199
    AddCriticalAppealDebuffByNumOfGd = 200
    AddCriticalAppealGimmickBuffByNumOfVo = 201
    AddCriticalAppealGimmickBuffByNumOfSp = 202
    AddCriticalAppealGimmickBuffByNumOfSk = 203
    AddCriticalAppealGimmickBuffByNumOfGd = 204
    AddCriticalAppealGimmickDebuffByNumOfVo = 205
    AddCriticalAppealGimmickDebuffByNumOfSp = 206
    AddCriticalAppealGimmickDebuffByNumOfSk = 207
    AddCriticalAppealGimmickDebuffByNumOfGd = 208
    AddCollaboVoltageBuffByNumOfVo = 209
    AddCollaboVoltageBuffByNumOfSp = 210
    AddCollaboVoltageBuffByNumOfSk = 211
    AddCollaboVoltageBuffByNumOfGd = 212
    AddCollaboVoltageDebuffByNumOfVo = 213
    AddCollaboVoltageDebuffByNumOfSp = 214
    AddCollaboVoltageDebuffByNumOfSk = 215
    AddCollaboVoltageDebuffByNumOfGd = 216
    AddCollaboVoltageGimmickBuffByNumOfVo = 217
    AddCollaboVoltageGimmickBuffByNumOfSp = 218
    AddCollaboVoltageGimmickBuffByNumOfSk = 219
    AddCollaboVoltageGimmickBuffByNumOfGd = 220
    AddCollaboVoltageGimmickDebuffByNumOfVo = 221
    AddCollaboVoltageGimmickDebuffByNumOfSp = 222
    AddCollaboVoltageGimmickDebuffByNumOfSk = 223
    AddCollaboVoltageGimmickDebuffByNumOfGd = 224
    AddSquadChangeEffectVoltageBuff = 225
    AddSquadChangeEffectRecastBuff = 226
    AddSquadChangeEffectCollaboBuff = 227
    AddSquadChangeEffectVoltageGimmickBuff = 228
    AddSquadChangeEffectRecastGimmickBuff = 229
    AddSquadChangeEffectCollaboGimmickBuff = 230
    AddPassiveSkillRateBuff = 231
    AddPassiveSkillRateDebuff = 232
    AddPassiveSkillRateGimmickBuff = 233
    AddPassiveSkillRateGimmickDebuff = 234
    RemovePassiveSkillRateBuff = 235
    RemovePassiveSkillRateDebuff = 236
    AddIndividualPassiveSkillRateBuff = 237
    AddIndividualPassiveSkillRateDebuff = 238
    AddIndividualPassiveSkillRateGimmickBuff = 239
    AddIndividualPassiveSkillRateGimmickDebuff = 240
    RemoveIndividualPassiveSkillRateBuff = 241
    RemoveIndividualPassiveSkillRateDebuff = 242
    AddAdditionalPassiveSkillRateBuff = 243
    AddAdditionalPassiveSkillRateDebuff = 244
    AddAdditionalPassiveSkillRateGimmickBuff = 245
    AddAdditionalPassiveSkillRateGimmickDebuff = 246
    RemoveAdditionalPassiveSkillRateBuff = 247
    RemoveAdditionalPassiveSkillRateDebuff = 248
    AddAccessoryPassiveSkillRateBuff = 249
    AddAccessoryPassiveSkillRateDebuff = 250
    AddAccessoryPassiveSkillRateGimmickBuff = 251
    AddAccessoryPassiveSkillRateGimmickDebuff = 252
    RemoveAccessoryPassiveSkillRateBuff = 253
    RemoveAccessoryPassiveSkillRateDebuff = 254
    AddNoteScoreUpLimitBuff = 255
    AddNoteScoreUpLimitDebuff = 256
    AddNoteScoreBaseBonusUpLimitBuff = 257
    AddNoteScoreBaseBonusUpLimitDebuff = 258
    AddNoteScoreUpLimitGimmickBuff = 259
    AddNoteScoreUpLimitGimmickDebuff = 260
    AddNoteScoreUpLimitBuffByCritical = 261
    AddDirectDamage = 262
    AddDirectRateDamage = 263
    AddStaminaBlockDebuff = 264
    AddStaminaBlockGimmickDebuff = 265
    AddSpSkillOverChargeBaseBonus = 266
    AddSpSkillVoltageBaseBonusByOverChargeMax = 267


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
    ST.AddVoltageByStamina,
    ST.AddVoltageByTechnique,
    ST.AddCollaboGaugeByStamina,
    ST.AddSpSkillOverChargeBaseBonus,
    ST.AddSpSkillVoltageBaseBonusByOverChargeMax,
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
    ST.AddVoltageByStamina,
    ST.AddVoltageByTechnique,
    ST.AddCollaboGaugeGimmickBuff,
    ST.AddCriticalRateGimmickBuff,
    ST.AddCriticalAppealGimmickBuff,
    ST.AddActionSkillRateGimmickBuff,
    ST.AddAppealGimmickBuff,
    ST.AddCollaboVoltageGimmickBuff,
    ST.AddVoltageGimmickBuff,
    ST.AddActionSkillRateGimmickDebuff,
    ST.AddVoltageGimmickDebuff,
    ST.AddCriticalAppealGimmickDebuff,
    ST.AddAppealGimmickDebuff,
    ST.AddCriticalRateGimmickDebuff,
    ST.AddCollaboGaugeGimmickDebuff,
    ST.AddCollaboGaugeByStamina,
    ST.AddNoteScoreUpLimitBuffByCritical,
    ST.AddSpSkillVoltageBaseBonusByOverChargeMax
}

MIXED_VALUE_SKILL_TYPES = {
    ST.AddVoltageBuff,
    ST.AddAppealBuff,
    ST.AddNoteScoreBaseBonusUpLimitBuff,
    ST.AddCriticalAppealBaseBonusChangingHpRateMax,
}
