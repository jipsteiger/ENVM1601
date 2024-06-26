def CSO_Pump_21(nodes, target=None):
    if nodes["j_21"].depth >= 1.8:
        target = 1
    if nodes["j_21"].depth <= 1.0:
        target = 0
    return "CSO_Pump_21", target


def p_21_2(nodes, target=None):
    if nodes["j_21"].depth >= 0.25:
        if nodes["j_2"].depth <= 1.5:
            target = 1
        elif (nodes["j_21"].depth >= 2.1) & (nodes["j_2"].depth <= 2.0):
            target = 1
        else:
            target = 0
    if nodes["j_21"].depth <= 0.10:
        target = 0

    return "p_21_2", target


def p_20_2(nodes, target=None):
    if nodes["j_20"].depth >= 0.25:
        if nodes["j_2"].depth <= 1.5:
            target = 1
        elif nodes["j_20"].depth >= 1.6:
            target = 1
        else:
            target = 0
    if nodes["j_20"].depth <= 0.10:
        target = 0
    return "p_20_2", target


def CSO_Pump_2(nodes, target=None):
    if nodes["j_2"].depth >= 1.8:
        target = 1
    if nodes["j_2"].depth <= 1.65:
        target = 0
    return "CSO_Pump_2", target


def p_2_1(nodes, target=None):
    if nodes["j_2"].depth >= 0.25:
        if nodes["j_1"].depth <= 1.3:
            target = 1
        elif nodes["j_2"].depth >= 1.1:
            target = 1
        else:
            target = 0

    if nodes["j_2"].depth <= 0.10:
        target = 0
    return "p_2_1", target


def WWTP_inlet(nodes, target=None):
    if nodes["j_1"].depth >= 0.15:
        target = 1
    if nodes["j_1"].depth <= 0.10:
        target = 0
    return "WWTP_inlet", target


def p10_1(nodes, target=None):
    if nodes["j_10"].depth >= 0.25:
        if nodes["j_1"].depth <= 1.5:
            target = 1
        elif nodes["j_10"].depth >= 2.1:
            target = 1
        else:
            target = 0

    if nodes["j_10"].depth <= 0.10:
        target = 0

    return "p10_1", target
