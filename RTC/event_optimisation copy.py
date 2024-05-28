import pyswmm
import pandas as pd
import os
import pulp as pl
import swmm_api
import numpy as np


NUMBER_OF_TIME_STEPS = 3  # Number of time steps that are used for prediction

WWTP_INLET_MAX = 1.167  # CMS
P_10_1_MAX = 0.694  # CMS
P_2_1_MAX = 0.500  # CMS
P_20_2_MAX = 0.015  # CMS
P_21_2_MAX = 0.0417  # CMS
CSO_PUMP_2_MAX = 0.5556  # CMS
CSO_PUMP_21_MAX = 0.0278  # CMS

CSO_CREST_HEIGHT = [1.83, 2.21, 2.48, 1.90, 2.16]  # Crest height of all weirs

junctions = ["j_1", "j_10", "j_2", "j_20", "j_21"]

JUNCTION_MAX_STORAGE = {}

# Calculate max storage in node based on weir crest height by using the storage curve
for i, junction in enumerate(junctions):
    storage_curve = pd.read_csv(
        f"RTC/event_optimisation_input_data/storage_curve_{int(junction.split('_')[-1])}.dat",
        delimiter=" ",
        skiprows=2,
        names=["depth", "area"],
    )
    max_storage = np.sum(
        storage_curve.loc[storage_curve.depth <= CSO_CREST_HEIGHT[i], "depth"]
        * storage_curve.loc[storage_curve.depth <= CSO_CREST_HEIGHT[i], "area"]
    )
    JUNCTION_MAX_STORAGE[junction] = max_storage

for file_number in range(1, 5 + 1):
    output = swmm_api.read_out_file(
        rf"RTC\event_optimisation_output_data\Dean Town_pyswmm_{file_number}.out"
    ).to_frame()
    j1_in = output["node"]["j_1"]["lateral_inflow"]
    j10_in = output["node"]["j_10"]["lateral_inflow"]
    j2_in = output["node"]["j_2"]["lateral_inflow"]
    j20_in = output["node"]["j_20"]["lateral_inflow"]
    j21_in = output["node"]["j_21"]["lateral_inflow"]

    with pyswmm.Simulation(
        f"RTC\event_optimisation_input_data\Dean Town_pyswmm_{file_number}.inp"
    ) as sim:
        nodes = pyswmm.Nodes(sim)
        links = pyswmm.Links(sim)

        time_step_size = 15 * 60
        sim.step_advance(time_step_size)
        number_of_steps_taken = 0
        for step in sim:
            number_of_steps_taken += 1
            if (nodes["j_1"].depth > 0.2) or (nodes["j_20"].depth > 0.2):
                initial_filling = [nodes[j].volume for j in junctions]
                prob = pl.LpProblem("DeanTown", pl.LpMinimize)  # type: ignore
                reservoir_delta_j_1 = 0
                reservoir_delta_j_10 = 0
                reservoir_delta_j_2 = 0
                reservoir_delta_j_20 = 0
                reservoir_delta_j_21 = 0
                equal_fill_obj = 0
                spill_obj = 0

                decision_indices = [
                    i for i in range(1, (12 * NUMBER_OF_TIME_STEPS + 1))
                ]

                x_vars = pl.LpVariable.dicts("x", decision_indices, 0, None, pl.LpContinuous)  # type: ignore

                # POTENTIAL DICT SLICING SOLUTION:
                #  # the dictionary
                # d = {1:2, 3:4, 5:6, 7:8}

                # # the subset of keys I'm interested in
                # l = (1,5)

                # print({k:d[k] for k in l if k in d})

                # Add equal filling degree to objective function, based on depth
                mean_depth = np.sum([nodes[j].depth for j in junctions]) / 5
                for junction in junctions:
                    equal_fill_obj += 1 * (nodes[junction].depth / mean_depth) ** 2

                # Add boundaries for each timestep
                for i in range(0, NUMBER_OF_TIME_STEPS):

                    # Setup objective function
                    if file_number == 1:  # Only file number 1 is during bathing season
                        for j, weight in enumerate([2, 2, 2, 2, 2, 1 / 500, 1 / 500]):
                            spill_obj += (
                                x_vars[j + 1 + 12 * i] * weight
                            )  # for each CSO (j+1) add weight, per timestep (+ 12 * i)
                    else:
                        for j, weight in enumerate([1, 2, 1, 1, 1, 1 / 500, 1 / 500]):
                            spill_obj += (
                                x_vars[j + 1 + 12 * i] * weight
                            )  # for each CSO (j+1) add weight, per timestep (+ 12 * i)
                    prob += equal_fill_obj + spill_obj

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

                    # Calculates the in and outflow of cso and pumps for each node, and sums it per amount
                    # of timesteps that are used as prediction
                    reservoir_delta_j_1 += (
                        x_vars[8 + 12 * i]
                        + x_vars[9 + 12 * i]
                        - x_vars[1 + 12 * i]
                        - x_vars[12 + 12 * i]
                    )
                    reservoir_delta_j_10 += -x_vars[2 + 12 * i] - x_vars[8 + 12 * i]
                    reservoir_delta_j_2 += (
                        x_vars[10 + 12 * i]
                        + x_vars[11 + 12 * i]
                        - x_vars[3 + 12 * i]
                        - x_vars[6 + 12 * i]
                        - x_vars[9 + 12 * i]
                    )
                    reservoir_delta_j_20 += -x_vars[4 + 12 * i] - x_vars[10 + 12 * i]
                    reservoir_delta_j_21 += -x_vars[5 + 12 * i] - x_vars[7 + 12 * i]

                # RESERVOIR VOLUMES
                # current volume + inflow - outflow cannot be more than the max volume in node
                prob += (
                    initial_filling[0]
                    + time_step_size
                    * (
                        np.sum(
                            j1_in[
                                number_of_steps_taken : number_of_steps_taken
                                + NUMBER_OF_TIME_STEPS
                            ]
                        )
                        + reservoir_delta_j_1
                    )
                ) <= JUNCTION_MAX_STORAGE["j_1"]
                prob += (
                    initial_filling[1]
                    + time_step_size
                    * np.sum(
                        j10_in[
                            number_of_steps_taken : number_of_steps_taken
                            + NUMBER_OF_TIME_STEPS
                        ]
                    )
                    + reservoir_delta_j_10
                ) <= JUNCTION_MAX_STORAGE["j_10"]
                prob += (
                    initial_filling[2]
                    + time_step_size
                    * np.sum(
                        j2_in[
                            number_of_steps_taken : number_of_steps_taken
                            + NUMBER_OF_TIME_STEPS
                        ]
                    )
                    + reservoir_delta_j_2
                ) <= JUNCTION_MAX_STORAGE["j_2"]
                prob += (
                    initial_filling[3]
                    + time_step_size
                    * np.sum(
                        j20_in[
                            number_of_steps_taken : number_of_steps_taken
                            + NUMBER_OF_TIME_STEPS
                        ]
                    )
                    + reservoir_delta_j_20
                ) <= JUNCTION_MAX_STORAGE["j_20"]
                prob += (
                    initial_filling[4]
                    + time_step_size
                    * np.sum(
                        j21_in[
                            number_of_steps_taken : number_of_steps_taken
                            + NUMBER_OF_TIME_STEPS
                        ]
                    )
                    + reservoir_delta_j_21
                ) <= JUNCTION_MAX_STORAGE["j_21"]

                prob.solve()
                print(prob.variables())
                break

        break
    break
    # Update pump controls
    # links["CSO_Pump_2"].target_setting = prob.variables()[32].varValue / CSO_PUMP_2_MAX
    # links["CSO_Pump_21"].target_setting = prob.variables()[33].varValue / CSO_PUMP_21_MAX
    # links["p10_1"].target_setting = prob.variables()[34].varValue / P_10_1_MAX
    # links["p_2_1"].target_setting = prob.variables()[35].varValue / P_2_1_MAX
    # links["p_20_2"].target_setting = prob.variables()[1].varValue / P_20_2_MAX
    # links["p_21_2"].target_setting = prob.variables()[2].varValue / P_21_2_MAX
    # links["WWTP_inlet"].target_setting = prob.variables()[3].varValue / WWTP_INLET_MAX


# x_vars[1] = cso_1 for timestep 1
# x_vars[2] = cso_10 for timestep 1
# x_vars[3] = cso_2 for timestep 1
# x_vars[4] = cso_20 for timestep 1
# x_vars[5] = cso_21 for timestep 1
# x_vars[6] = CSO_pump_2 for timestep 1
# x_vars[7] = CSO_pump_21 for timestep 1
# x_vars[8] = pump_10_1 for timestep 1
# x_vars[9] = pump_2_1 for timestep 1
# x_vars[10] = pump_20_2 for timestep 1
# x_vars[11] = pump_21_2 for timestep 1
# x_vars[12] = WWTP_inlet for timestep 1
# x_vars[13] = cso_1 for timestep 2
# x_vars[14] = cso_10 for timestep 2
# x_vars[15] = cso_2 for timestep 2
# x_vars[16] = cso_20 for timestep 2
# x_vars[17] = cso_21 for timestep 2
# x_vars[18] = CSO_pump_2 for timestep 2
# x_vars[19] = CSO_pump_21 for timestep 2
# x_vars[20] = pump_10_1 for timestep 2
# x_vars[21] = pump_2_1 for timestep 2
# x_vars[22] = pump_20_2 for timestep 2
# x_vars[23] = pump_21_2 for timestep 2
# x_vars[24] = WWTP_inlet for timestep 2
# etc.
