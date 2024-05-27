import pyswmm
import pandas as pd
import os 
from pulp import *
import swmm_api 


file = 'RTC/data/Dean Town_pyswmm.inp'

#this is a file that of the event that is ran beforehand
file_2 = 'RTC/data/Dean Town_pswmm.inp'
fh = swmm_api.read_out_file(file_2)
output_df = fh.to_frame()
j_1_r = output_df['j_1']['Lateral_inflow'] #get inflow from run-off into this node

with pyswmm.Simulation(file) as sim:
    nodes = pyswmm.Nodes(sim)
    links = pyswmm.Links(sim)
    
    sim.step_advance(60 * 15)
    
    for step in sim:
        if nodes['j_1'].depth > 0.2 or nodes['j_20'].depth > 0.2: #only optimise during and after rain while system is full
            
            initial_filling = [nodes[k].volume for k in nodes]
            prob = Lp.Problem('DeanTown', LpMinimize)
            
            decision_indicices = [i for i in range(1, 10)]
            
            x_vars = LpVariable.dicts('x', decision_indices, 0, None, LpContinuous)
            
            #OBJECTIVE FUNCTION
            prop += (x_vars * [1, 1, 1, 1, 1/500, 1, 1, 1,1 1/500]) 
            #Above is objective functions for different nodes
            #add equal filling degree(FD) somwhow for all i (FD_i -FD_mean)**2
            
            #SET CONSTRAINTS CSO VALUES
            prob += x_vars[3] >= 0   #Add boundary condition
            prob += x_vars[5] >= 0   #CSO can only be larger than 0 
            
            
            #SET CONSTRAINTS ON PUMPS
            prob += x_vars[1] <= 1.22 #Pump can only me smaller than its capacity
            prob += x_vars[0] >= 0 #Can not below 0
            
            #RESERVOIR VOLUMES
            #current volume + inflow - outflow cannot be more than the max volume
            prob += (initial_filling[0] + j_1_r[number_of_steps_taken] - x_vars[1] - x_vars[2] - x_vars[3] + x_vars[4]) <= max_volume_in_j_1
            #current volume + infows - outflows cannot be less than 0
            prob += (initial_filling[0] + j_1_r[number_of_steps_taken] - x_vars[1] - x_vars[2] - x_vars[3] + x_vars[4]) >= max_volume_in_j_1

            # to look 2 steps ahead!: WHERE x_vars[7] and 8 and 9, is pumped CSO for 2nd timestep!
            prob += (initial_filling[0] + j_1_r[number_of_steps_taken+1] - x_vars[1] - x_vars[2] - x_vars[3] + x_vars[4] + x_vars[7] + x_vars[8] + x_vars[9]) <= max_volume_in_j_1
            prob += (initial_filling[0] + j_1_r[number_of_steps_taken+1] - x_vars[1] - x_vars[2] - x_vars[3] + x_vars[4] + x_vars[7] + x_vars[8] + x_vars[9]) >= max_volume_in_j_1

            prob.solve()
            
            links['pump_1'].target_setting = prob.variables()[1-1].varValue / 1.22 #back to python convetion from 1 index to 0 index, and divide my max pump setting
            #only need to do this for pumps
            
            
            