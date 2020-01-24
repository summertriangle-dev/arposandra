from ..wave_cs_enums import WaveType
from ..wave_description_base import WaveMissionDescriber

######################################################

JA = WaveMissionDescriber()

# fmt: off

JA.missions[WaveType.MaxVoltage] = "1回で$1ボルテージを獲得する"
JA.missions[WaveType.UseCardUniq] = "$1人のスクールアイドルでアピールする"
JA.missions[WaveType.JudgeSuccessPerfect] = "WONDERFUL以上の判定を$1回出す"
JA.missions[WaveType.JudgeSuccessGreat] = "GREAT以上の判定を$1回出す"
JA.missions[WaveType.JudgeSuccessGood] = "NICE以上の判定を$1回出す"
JA.missions[WaveType.TriggerSp] = "SP特技で合計$1ボルテージを獲得する"
JA.missions[WaveType.GotVoltage] = "合計$1ボルテージを獲得する"

# fmt: on
