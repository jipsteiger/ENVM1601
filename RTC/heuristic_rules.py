def p10_1(nodes, target=None):
    if (nodes["j_10"].depth >= 0.25):
        target = 1
    if nodes["j_10"].depth <= 0.10:
        target = 0
    # if (nodes["j_10"].depth <= 0.20) & (nodes["j_1"].depth >= 0.20):
    #     target = 1
    return 'p10_1', target 

def p_21_2(nodes, target=None):
    # if (nodes["j_2"].depth >= 0.20) & (nodes["j_21"].depth <= 0.15):
    #     target = 0
    if nodes["j_21"].depth >= 0.25:
        target = 1
    if nodes["j_21"].depth <= 0.10:
        target = 0    
    return 'p_21_2', target
    
def WWTP_inlet(nodes, target=None):
    if nodes["j_1"].depth >= 0.25:
        target = 1
    if nodes["j_1"].depth <= 0.10:
        target = 0
    return 'WWTP_inlet', target

def CSO_Pump_21(nodes, target=None):
    if nodes["j_21"].depth >= 1.10:
        target = 1
    if nodes["j_21"].depth <= 0.90:
        target = 0
    return 'CSO_Pump_21', target

def p_2_1(nodes, target=None):
    if nodes["j_2"].depth >= 0.25:
        target = 1
    if nodes["j_2"].depth <= 0.10:
        target = 0    
    return 'p_2_1', target

def CSO_Pump_2(nodes, target=None):
    if nodes["j_2"].depth >= 2.5:
        target = 1
    if nodes["j_2"].depth <= 2.0:
        target = 0    
    return 'CSO_Pump_2', target