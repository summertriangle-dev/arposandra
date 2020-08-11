from typing import Tuple, List, Iterable, Callable, TypeVar, Optional, Dict
from contextlib import contextmanager

_coding_contexts = []


@contextmanager
def coding_context(it):
    _coding_contexts.append(it)
    try:
        yield
    finally:
        _coding_contexts.pop()


def get_coding_context():
    return _coding_contexts[-1]


## TT

T = TypeVar("T")


def find_first(it: Iterable[T], matching: Callable[[T], bool]) -> Optional[T]:
    for x in it:
        if matching(x):
            return x
    return None


def cell_content(cell_type, required_grade, stat, value, training_tree_cell_item_set_m_id):
    r = {
        "type": cell_type,
        "req_grade": required_grade,
        "req_mats": training_tree_cell_item_set_m_id,
    }
    if cell_type == 2:
        r["stat"] = stat
        r["value"] = value
    return r


def construct_tt_from_sql_shape(t: Tuple[List[Tuple[int, int, int]], List[Tuple[int, int]]]):
    root = find_first(t, lambda x: x[0] == x[1])
    if not root:
        raise ValueError("TT shape has no root node")

    level = {root[0]: (0, root[2] - 1)}
    stack = [[None, None, None, None, None]]
    stack[0][root[2] - 1] = (root[0], root[2], {"type": 1, "req_grade": 0})
    locks = {}

    for cid, pid, conntype, *cell_params in filter(lambda x: x[0] != root[0], t):
        l, pdx = level[pid]

        if conntype == 100:  # Forward connection
            parent_params = stack[l][pdx][2]
            my_params = cell_content(*cell_params)

            level[cid] = (l + 1, pdx)
            if l + 1 < len(stack):
                t = stack[l + 1]
                t[pdx] = (cid, conntype, my_params)
            else:
                template = [None, None, None, None, None]
                template[pdx] = (cid, conntype, my_params)
                stack.insert(l + 1, template)

            if parent_params["req_grade"] < my_params["req_grade"]:
                locks[l + 1] = my_params["req_grade"]
        elif conntype == 101:  # Up connection
            level[cid] = (l, pdx - 1)
            stack[l][pdx - 1] = (cid, conntype, cell_content(*cell_params))
        elif conntype == 102:  # Down connection
            level[cid] = (l, pdx + 1)
            stack[l][pdx + 1] = (cid, conntype, cell_content(*cell_params))

    return stack, list(locks.items())


## Icon generation

IFI_FRAME = {
    1: "s",  # R "silver"
    2: "g",  # SR "gold"
    3: "r",  # UR "rainbow"
}
IFI_ATTR = {
    1: "m",  # Smile
    2: "p",  # Pure
    3: "c",  # Cool
    4: "a",  # Active
    5: "n",  # Natural
    6: "e",  # Elegant
}
IFI_ROLE = {
    1: "v",  # Vo
    2: "p",  # Sp
    3: "u",  # Gd
    4: "k",  # Sk
}

IFI_FRAME_REV = {v: k for k, v in IFI_FRAME.items()}
IFI_ATTR_REV = {v: k for k, v in IFI_ATTR.items()}
IFI_ROLE_REV = {v: k for k, v in IFI_ROLE.items()}


def icon_frame_info(rarity: int, role: int, ctype: int):
    cs = IFI_FRAME.get(rarity, "z")
    rs = IFI_ROLE.get(role, "x")
    ts = IFI_ATTR.get(ctype, "y")
    return "".join([cs, rs, ts])


def from_frame_info(fi: str):
    cs = IFI_FRAME_REV.get(fi[0], 0)
    rs = IFI_ROLE_REV.get(fi[1], 0)
    ts = IFI_ATTR_REV.get(fi[2], 0)
    return (cs, rs, ts)
