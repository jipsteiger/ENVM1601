prob = 0
x_vars = []
CSO_PUMP_21_MAX = 0
var_list = []
links = []
i = 1


# x_vars[7] = CSO_pump_21 for timestep 1
#  Add PUMP boundary conditions                   
prob += x_vars[7 + 12 * i] >= 0
...
prob += x_vars[7 + 12 * i] <= CSO_PUMP_21_MAX
...
links["CSO_Pump_21"].target_setting = (
    prob.variables()[var_list.index("x_7")].varValue / CSO_PUMP_21_MAX
                )
