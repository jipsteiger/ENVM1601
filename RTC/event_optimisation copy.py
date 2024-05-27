import pyswmm
import pandas as pd
import os 
import pulp as pl
import swmm_api 
import numpy as np


NUMBER_OF_TIME_STEPS = 3 #Number of time steps that are used for prediction

WWTP_INLET_MAX = 1.167 #CMS
P_10_1_MAX = 0.694 #CMS
P_2_1_MAX = 0.500 #CMS
P_20_2_MAX = 0.015 #CMS
P_21_2_MAX = 0.0417 #CMS
CSO_PUMP_2_MAX = 0.5556 #CMS
CSO_PUMP_21_MAX = 0.0278 #CMS

junctions = ['j_1', 'j_10', 'j_2', 'j_20', 'j_21']

for file_number in range(1, 5 + 1):
    output = swmm_api.read_out_file(fr"RTC\event_optimisation_output_data\\
        Dean Town_pyswmm_{file_number}.out").to_frame()
    j1_in = output['node']['j_1']['lateral_inflow']
    j10_in = output['node']['j_10']['lateral_inflow']
    j2_in = output['node']['j_2']['lateral_inflow']
    j20_in = output['node']['j_20']['lateral_inflow']
    j21_in = output['node']['j_21']['lateral_inflow']
    
    with pyswmm.Simulation(fr"RTC\event_optimisation_input_data\Dean Town_pyswmm_{file_number}.inp") as sim:
        nodes = pyswmm.Nodes(sim)
        links = pyswmm.Links(sim)

        sim.step_advance(15 * 60)
        number_of_steps_taken = 0
        for step in sim:
            number_of_steps_taken += 1
            if (nodes['j_1'].depth > 0.2) or (nodes['j_20'].depth > 0.2):
                initial_filling = [nodes[j].volume for j in junctions]
                prob = pl.LpProblem('DeanTown', pl.LpMinimize) # type: ignore
                
                decision_indices = [i for i in range(1, (12 * NUMBER_OF_TIME_STEPS + 1))]

                x_vars = pl.LpVariable.dicts("x", decision_indices, 0, None, pl.LpContinious) # type: ignore 
                
                # Setup objective function
                if file_number == 1: #Only file number 1 is during bathing season
                    for i, weight in enumerate([2, 2, 2, 2, 2, 1 / 500, 1 / 500]):
                        prob += decision_indices[i+1::12] * weight
                    
                else:
                    for i, weight in enumerate([1, 2, 1, 1, 1, 1 / 500, 1 / 500]):
                        prob += decision_indices[i+1::12] * weight
                
                # Add equal filling degree to objective function, based on depth
                mean_depth = np.sum([nodes[j].depth for j in junctions]) / 5
                for junction in junctions:
                    prob += 1 * (nodes[junction].depth / mean_depth)**2
                
                        
                # Add boundaries for each timestep        
                for i in range(0, NUMBER_OF_TIME_STEPS):
                    # Add CSO boundary condition
                    prob += x_vars[1 + 12 * i] >= 0
                    prob += x_vars[2 + 12 * i] >= 0
                    prob += x_vars[3 + 12 * i] >= 0
                    prob += x_vars[4 + 12 * i] >= 0
                    prob += x_vars[5 + 12 * i] >= 0
                    
                    # Add PUMP boundary conditions
                    prob += x_vars[6 + 12 * i] >= 0
                    prob += x_vars[7 + 12 * i] >= 0
                    prob += x_vars[8 + 12 * i] >= 0
                    prob += x_vars[9 + 12 * i] >= 0
                    prob += x_vars[10 + 12 * i] >= 0
                    prob += x_vars[11 + 12 * i] >= 0
                    prob += x_vars[12 + 12 * i] >= 0
                    
                    prob += x_vars[6 + 12 * i] <= CSO_PUMP_2_MAX
                    prob += x_vars[7 + 12 * i] <= CSO_PUMP_21_MAX
                    prob += x_vars[8 + 12 * i] <= P_10_1_MAX
                    prob += x_vars[9 + 12 * i] <= P_2_1_MAX
                    prob += x_vars[10 + 12 * i] <= P_20_2_MAX
                    prob += x_vars[11 + 12 * i] <= P_21_2_MAX
                    prob += x_vars[12 + 12 * i] <= WWTP_INLET_MAX
                   
                    #RESERVOIR VOLUMES
                    #current volume + inflow - outflow cannot be more than the max volume in node
                    prob += (initial_filling[0] +\
                        np.sum(j1_in[number_of_steps_taken:number_of_steps_taken+NUMBER_OF_TIME_STEPS]) \
                        + np.sum(x_vars[8::12]) + np.sum(x_vars[9::12]) \
                        - np.sum(x_vars[1::12]) - np.sum(x_vars[12::12])) \
                            <= max_j_1_volume
                    prob += (initial_filling[1] \
                        + np.sum(j10_in[number_of_steps_taken:number_of_steps_taken+NUMBER_OF_TIME_STEPS]) \
                        - np.sum(x_vars[2::12]) - np.sum(x_vars[8::12])) \
                            <= max_j_10_volume
                    prob += (initial_filling[2] \
                        + np.sum(j2_in[number_of_steps_taken:number_of_steps_taken+NUMBER_OF_TIME_STEPS]) \
                        + np.sum(x_vars[10::12]) + np.sum(x_vars[11::12]) \
                        - np.sum(x_vars[3::12]) - np.sum(x_vars[6::12]) - np.sum(x_vars[9::12])) \
                            <= max_j_2_volume
                    prob += (initial_filling[3] \
                        + np.sum(j20_in[number_of_steps_taken:number_of_steps_taken+NUMBER_OF_TIME_STEPS])
                        - np.sum(x_vars[4::12]) - np.sum(x_vars[20::12])) \
                            <= max_j_20_volume
                    prob += (initial_filling[4] \
                        + np.sum(j21_in[number_of_steps_taken:number_of_steps_taken+NUMBER_OF_TIME_STEPS]) \
                        - np.sum(x_vars[5::12]) - np.sum(x_vars[7::12])) \
                            <= max_j_21_volume
                    
                    prob.solve()
                    
                    # Update pump controls
                    links["CSO_Pump_2"].target_setting = prob.variables()[6].varValue / CSO_PUMP_2_MAX
                    links["CSO_Pump_21"].target_setting = prob.variables()[7].varValue / CSO_PUMP_21_MAX
                    links["p10_1"].target_setting = prob.variables()[8].varValue / P_10_1_MAX
                    links["p_2_1"].target_setting = prob.variables()[9].varValue / P_2_1_MAX
                    links["p_20_2"].target_setting = prob.variables()[10].varValue / P_20_2_MAX
                    links["p_21_2"].target_setting = prob.variables()[11].varValue / P_21_2_MAX                  
                    links["WWTP_inlet"].target_setting = prob.variables()[12].varValue / WWTP_INLET_MAX
                    
                          
#x_vars[1] = cso_1 for timestep 1
#x_vars[2] = cso_10 for timestep 1
#x_vars[3] = cso_2 for timestep 1
#x_vars[4] = cso_20 for timestep 1
#x_vars[5] = cso_21 for timestep 1
#x_vars[6] = CSO_pump_2 for timestep 1
#x_vars[7] = CSO_pump_21 for timestep 1
#x_vars[8] = pump_10_1 for timestep 1
#x_vars[9] = pump_2_1 for timestep 1
#x_vars[10] = pump_20_2 for timestep 1
#x_vars[11] = pump_21_2 for timestep 1
#x_vars[12] = WWTP_inlet for timestep 1
#x_vars[13] = cso_1 for timestep 2
#x_vars[14] = cso_10 for timestep 2
#x_vars[15] = cso_2 for timestep 2
#x_vars[16] = cso_20 for timestep 2
#x_vars[17] = cso_21 for timestep 2
#x_vars[18] = CSO_pump_2 for timestep 2
#x_vars[19] = CSO_pump_21 for timestep 2                
#x_vars[20] = pump_10_1 for timestep 2
#x_vars[21] = pump_2_1 for timestep 2
#x_vars[22] = pump_20_2 for timestep 2
#x_vars[23] = pump_21_2 for timestep 2
#x_vars[24] = WWTP_inlet for timestep 2  
#etc.      