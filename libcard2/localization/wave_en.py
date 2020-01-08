from ..wave_cs_enums import WaveType
from ..wave_description_base import WaveMissionDescriber

######################################################

EN = WaveMissionDescriber()

# fmt: off

EN.missions[WaveType.MaxVoltage] = "Earn at least $1 voltage with a single note"
EN.missions[WaveType.UseCardUniq] = "Perform with at least $1 different idols"
EN.missions[WaveType.JudgeSuccessPerfect] = "Hit at least $1 WONDERFUL notes"
EN.missions[WaveType.JudgeSuccessGreat] = "Hit at least $1 GREAT notes"
EN.missions[WaveType.JudgeSuccessGood] = "Hit at least $1 NICE notes"
EN.missions[WaveType.TriggerSp] = "Earn at least $1 voltage from an SP burst"
EN.missions[WaveType.GotVoltage] = "Earn at least $1 total voltage"

# fmt: on
