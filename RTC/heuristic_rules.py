# def CSO_Pump_21(nodes, target=None):
#     """Checks wether target value for specific pump needs to be updated

#     Args:
#         nodes (_type_): Contains depth information
#         target (_type_, optional): Initialization of target. Defaults to None.

#     Returns:
#         _type_: Name of to be updated pump, target value of that pump
#     """
#     if nodes["j_21"].depth >= 1.8:
#         target = 1
#     if nodes["j_21"].depth <= 1.5:
#         target = 0
#     return "CSO_Pump_21", target


# def p_21_2(nodes, target=None):
#     if nodes["j_21"].depth >= 1.9:
#         target = 1

#     if (nodes["j_21"].depth >= 0.25) and (nodes["j_2"].depth <= 2.0):
#         target = 1

#     if (nodes["j_21"].depth <= 1.9) and (nodes["j_2"].depth >= 2.1):
#         target = 0

#     if nodes["j_21"].depth <= 0.10:
#         target = 0

#     return "p_21_2", target


# def p_20_2(nodes, target=None):
#     if nodes["j_20"].depth >= 0.25:
#         target = 1

#     if (nodes["j_20"].depth <= 1.5) and (nodes["j_2"].depth >= 2.0):
#         target = 0

#     if nodes["j_20"].depth <= 0.10:
#         target = 0
#     return "p_20_2", target


# def CSO_Pump_2(nodes, target=None):
#     if nodes["j_2"].depth >= 2.0:
#         target = 1
#     if nodes["j_2"].depth <= 1.9:
#         target = 0
#     return "CSO_Pump_2", target


# def p_2_1(nodes, target=None):
#     if nodes["j_2"].depth >= 0.15:
#         target = 1
#     elif (nodes["j_20"].depth >= 0.25) or (nodes["j_21"].depth >= 0.25):
#         target = 1
#     if nodes["j_2"].depth <= 0.10:
#         target = 0
#     return "p_2_1", target


# def WWTP_inlet(nodes, target=None):
#     if (
#         (nodes["j_1"].depth >= 0.25)
#         or (nodes["j_10"].depth >= 0.25)
#         or (nodes["j_2"].depth >= 0.25)
#         or (nodes["j_20"].depth >= 0.25)
#         or (nodes["j_21"].depth >= 0.25)
#     ):
#         target = 1
#     else:
#         target = 0
#     if nodes["j_1"].depth <= 0.05:
#         target = 0
#     return "WWTP_inlet", target


# def p10_1(nodes, target=None):
#     if nodes["j_10"].depth >= 0.25:
#         if (
#             (nodes["j_2"].depth >= 0.25)
#             or (nodes["j_20"].depth >= 0.25)
#             or (nodes["j_21"].depth >= 0.25)
#             or (nodes["j_1"].depth >= 0.25)
#         ):
#             target = 0
#         else:
#             target = 1
#         if nodes["j_10"].depth >= 2.0:
#             target = 1
#     if nodes["j_10"].depth <= 0.10:
#         target = 0


#     return "p10_1", target
def CSO_Pump_21(nodes, target=None):
    """Checks wether target value for specific pump needs to be updated

    Args:
        nodes (_type_): Contains depth information
        target (_type_, optional): Initialization of target. Defaults to None.

    Returns:
        _type_: Name of to be updated pump, target value of that pump
    """
    if nodes["j_21"].depth >= 1.4:
        target = 1
    if (nodes["j_21"].depth >= 0.8) & (nodes["j_2"].depth >= 1.5):  # NOT NECCESARYY!?
        target = 1
    if nodes["j_21"].depth <= 0.7:
        target = 0
    return "CSO_Pump_21", target


def p_21_2(nodes, target=None):
    if nodes["j_21"].depth >= 0.25:
        if nodes["j_2"].depth <= 1.5:
            target = 1
        elif (nodes["j_21"].depth >= 1.8) & (nodes["j_2"].depth <= 2.0):
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
        elif nodes["j_20"].depth >= 1.7:
            target = 1
        else:
            target = 0
    if nodes["j_20"].depth <= 0.10:
        target = 0
    return "p_20_2", target


def CSO_Pump_2(nodes, target=None):
    if nodes["j_2"].depth >= 2.1:
        target = 1
    if nodes["j_2"].depth <= 1.5:
        target = 0
    return "CSO_Pump_2", target


def p_2_1(nodes, target=None):
    if nodes["j_2"].depth >= 0.25:
        if nodes["j_1"].depth <= 0.5:
            target = 1
        elif nodes["j_2"].depth >= 1.1:
            target = 1
        else:
            target = 0

    if nodes["j_2"].depth <= 0.10:
        target = 0
    return "p_2_1", target


def WWTP_inlet(nodes, target=None):
    if nodes["j_1"].depth >= 0.25:
        target = 1
    if nodes["j_1"].depth <= 0.10:
        target = 0
    return "WWTP_inlet", target


def p10_1(nodes, target=None):
    if nodes["j_10"].depth >= 0.25:
        if nodes["j_1"].depth <= 0.5:
            target = 1
        elif nodes["j_10"].depth >= 1.8:
            target = 1
        else:
            target = 0

    if nodes["j_10"].depth <= 0.10:
        target = 0

    return "p10_1", target
