import sys

from libcard2 import skill_cs_enums

SKILL_ID_REVERSE_MAP = {
    v: k for k, v in skill_cs_enums.ST.__dict__.items() if k[0].upper() == k[0] and k[0].isalpha()
}


def audit(lang):
    target = __import__(f"libcard2.localization.skills_{lang}", fromlist=[lang.upper()])
    target = getattr(target, lang.upper())

    nactual = len(SKILL_ID_REVERSE_MAP)
    ncovered = 0
    for sid, symbol in SKILL_ID_REVERSE_MAP.items():
        if sid not in target.skill_effect.data:
            print(f"# Missing: ST.{symbol}")
        else:
            ncovered += 1
    print(f"# {ncovered} skills described. {nactual - ncovered} missing.")


def main():
    langs = [l.lower() for l in sys.argv[1:]]
    for lang in langs:
        print(f"# ------- AUDIT for {lang} --------------------------------------")
        audit(lang)
        print()


if __name__ == "__main__":
    main()
