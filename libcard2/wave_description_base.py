import re

from .wave_cs_enums import WaveType

LANGUAGE_DEFINITION_JA = {
    WaveType.MaxVoltage: re.compile("1回で([0-9]+)ボルテージを獲得する"),
    WaveType.UseCardUniq: re.compile("([0-9]+)人のスクールアイドルでアピールする"),
    # hypothetical
    WaveType.JudgeSuccessPerfect: re.compile("WONDERFUL以上の判定を([0-9]+)回出す"),
    WaveType.JudgeSuccessGreat: re.compile("GREAT以上の判定を([0-9]+)回出す"),
    WaveType.JudgeSuccessGood: re.compile("NICE以上の判定を([0-9]+)回出す"),
    WaveType.TriggerSp: re.compile("SP特技で合計([0-9]+)ボルテージを獲得する"),
    WaveType.GotVoltage: re.compile("合計([0-9]+)ボルテージを獲得する"),
}


class WaveMissionDescriber(object):
    VAR_SUB = re.compile(r"\$([0-9]+)")

    def __init__(self):
        self.missions = {}

    def sub_with(self, match, tlfmt):
        return self.VAR_SUB.sub(lambda x: match.group(int(x.group(1))), tlfmt)

    def translate(self, langdef, desc):
        for wid, pat in langdef.items():
            m = pat.match(desc)
            if m:
                return self.sub_with(m, self.missions.get(wid))

        return desc
