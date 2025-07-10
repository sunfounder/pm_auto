DEFAULT_EFFECT = "rainbow"

EFFECT_LIST = [
    "solid",
    "breathing",
    "rainbow",
    "rainbow_reverse",
    "spin",
    "dual_spin",
    "rainbow_spin",
    "shift_spin",
]

def get_effect(effect_name):
    if effect_name == "solid":
        from .solid import solid
        return solid
    elif effect_name == "breathing":
        from .breathing import breathing
        return breathing
    elif effect_name == "rainbow":
        from .rainbow import rainbow
        return rainbow
    elif effect_name == "rainbow_reverse":
        from .rainbow import rainbow_reverse
        return rainbow_reverse
    elif effect_name == "spin":
        from .spin import spin
        return spin
    elif effect_name == "dual_spin":
        from .spin import dual_spin
        return dual_spin
    elif effect_name == "rainbow_spin":
        from .rainbow_spin import rainbow_spin
        return rainbow_spin
    elif effect_name == "shift_spin":
        from .shift_spin import shift_spin
        return shift_spin
    else:
        raise ValueError(f"Unknown effect: {effect_name}")