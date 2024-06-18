import pyswmm  # type: ignore
import pandas as pd  # type: ignore
import os
import pulp as pl  # type: ignore
import swmm_api as sa  # type: ignore
import numpy as np
from RTC.heuristic_rules_simulation import process_output
import datetime as dt


NUMBER_OF_TIME_STEPS = 9  # Number of time steps that are used for prediction

WWTP_INLET_MAX = 1.167  # CMS
P_10_1_MAX = 0.694  # CMS
P_2_1_MAX = 0.500  # CMS
P_20_2_MAX = 0.015  # CMS
P_21_2_MAX = 0.0417  # CMS
CSO_PUMP_2_MAX = 0.5556  # CMS
CSO_PUMP_21_MAX = 0.0278  # CMS

EVENT_NAME = [
    "Major event june",
    "Minor event december",
    "Multiple average events september",
    "3 major events february",
    "Peak intensity event february",
]

CSOS = {
    "cso_1": 0,
    "cso_20": 0,
    "cso_2a": 0,
    "cso_21a": 0,
    "cso_10": 0,
    "cso_21b": 0,
    "cso_2b": 0,
}

CSO_CREST_HEIGHT = [1.83, 2.21, 2.48, 1.90, 2.16]  # Crest height of all weirs

junctions = ["j_1", "j_10", "j_2", "j_20", "j_21"]

EQUAL_FILLING_WEIGHT = 10

JUNCTION_MAX_STORAGE = {}

som = 0
cso_sum = 0

# Calculate max storage in node based on weir crest height by using the storage curve
for i, junction in enumerate(junctions):
    storage_curve = pd.read_csv(
        f"RTC/event_optimisation_input_data/storage_curve_{int(junction.split('_')[-1])}.dat",
        delimiter=" ",
        skiprows=2,
        names=["depth", "area"],
    )
    max_storage = np.sum(
        0.01  # it calculates area not volume otherwise!
        * storage_curve.loc[storage_curve.depth <= CSO_CREST_HEIGHT[i], "area"]
    )
    JUNCTION_MAX_STORAGE[junction] = max_storage

for file_number in range(1, 5 + 1):
    output_inflow = sa.read_out_file(
        rf"RTC\event_optimisation_output_data\Dean Town_pyswmm_{file_number}.out"
    ).to_frame()
    j1_in = output_inflow["node"]["j_1"]["lateral_inflow"] * 1000
    j10_in = output_inflow["node"]["j_10"]["lateral_inflow"] * 1000
    j2_in = output_inflow["node"]["j_2"]["lateral_inflow"] * 1000
    j20_in = output_inflow["node"]["j_20"]["lateral_inflow"] * 1000
    j21_in = output_inflow["node"]["j_21"]["lateral_inflow"] * 1000

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
                filling_penalty = pl.LpVariable("equal_fill_obj", lowBound=0)
                # Add boundaries for each timestep
                for i in range(0, NUMBER_OF_TIME_STEPS):
                    # Setup objective function values
                    if file_number == 1:  # Only file number 1 is during bathing season
                        for j, weight in enumerate([2, 2, 2, 2, 2, 1 / 500, 1 / 500]):
                            spill_obj += (
                                x_vars[j + 1 + 12 * i] * weight
                            )  # for each CSO (j+1) multiply by weight, per timestep (+ 12 * i)
                    else:
                        for j, weight in enumerate([1, 2, 1, 1, 1, 1 / 500, 1 / 500]):
                            spill_obj += (
                                x_vars[j + 1 + 12 * i] * weight
                            )  # for each CSO (j+1) multiply by weight, per timestep (+ 12 * i)

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

                    reservoir_delta_j_21 += (
                        -x_vars[5 + 12 * i] - x_vars[7 + 12 * i] - x_vars[11 + 12 * i]
                    )

                    # TODO: junction filled volume has to be used in the i loop, has to be calculated for each time step.
                    # If that doesnt work, add to the the function objective something that penalises volume in all nodes
                    # except for j_1. And promotes usage of pumping to j_1.

                    # CALCULATE RESERVOIR VOLUMES
                    # current volume + timedelta * (inflow (precipitation and connections) - outflow(pump & cso))
                    # cannot be more than the max storage volume in node
                    junction_filled_volume = {}
                    junction_filled_volume["j_1"] = initial_filling[
                        0
                    ] + time_step_size * (
                        np.sum(
                            j1_in[
                                number_of_steps_taken : number_of_steps_taken + (i + 1)
                            ]
                        )
                        + reservoir_delta_j_1
                    )
                    junction_filled_volume["j_10"] = initial_filling[
                        1
                    ] + time_step_size * np.sum(
                        j10_in[number_of_steps_taken : number_of_steps_taken + (i + 1)]
                        + reservoir_delta_j_10
                    )
                    junction_filled_volume["j_2"] = initial_filling[
                        2
                    ] + time_step_size * np.sum(
                        j2_in[number_of_steps_taken : number_of_steps_taken + (i + 1)]
                        + reservoir_delta_j_2
                    )

                    junction_filled_volume["j_20"] = initial_filling[
                        3
                    ] + time_step_size * np.sum(
                        j20_in[number_of_steps_taken : number_of_steps_taken + (i + 1)]
                        + reservoir_delta_j_20
                    )

                    junction_filled_volume["j_21"] = initial_filling[
                        4
                    ] + time_step_size * np.sum(
                        j21_in[number_of_steps_taken : number_of_steps_taken + (i + 1)]
                        + reservoir_delta_j_21
                    )

                    # SET RESERVOIR BOUNDARY CONDITIONS ALSO MINIMUM ZERO, AND CALC. FILLING DEGREE
                    storage_depth = {}
                    storage_total_depth = 0
                    for junction in junctions:
                        prob += (
                            junction_filled_volume[junction]
                            <= JUNCTION_MAX_STORAGE[junction]
                        )
                        prob += junction_filled_volume[junction] >= 0

                        if junction != "j_1":
                            filling_penalty += (
                                junction_filled_volume[junction]
                                / JUNCTION_MAX_STORAGE[junction]
                            ) * 100

                        storage_depth[junction] = (
                            junction_filled_volume[junction]
                            / JUNCTION_MAX_STORAGE[junction]
                        )
                        storage_total_depth += (
                            junction_filled_volume[junction]
                            / JUNCTION_MAX_STORAGE[junction]
                        )

                # TODO: Add all above to the i loop.

                storage_mean_depth = storage_total_depth / len(junctions)

                # Calculate equal filling degree to objective function, based on filling degree per junction
                # THIS SECTION IS PARTLY PROVIDED BY CHATGPT DUE TO JANKY ABSOLUTES
                abs_diff = {}
                equal_fill_obj = pl.LpVariable("equal_fill_obj", lowBound=0)
                for junction in storage_depth:
                    break
                    # Create a new variable for the absolute difference
                    abs_diff[junction] = pl.LpVariable(
                        f"abs_diff_{junction}", lowBound=0
                    )

                    # Add constraints for the absolute difference
                    prob += abs_diff[junction] >= (
                        storage_depth[junction] - storage_mean_depth
                    )
                    prob += abs_diff[junction] >= -(
                        storage_depth[junction] - storage_mean_depth
                    )

                    # Add the weighted absolute difference to the objective
                    equal_fill_obj += EQUAL_FILLING_WEIGHT * abs_diff[junction]

                # Set FUNCTION OBJECTIVE

                prob += spill_obj + filling_penalty  # + equal_fill_obj

                prob.solve()

                # Create list of weirdly ordered problem variables to index can be found
                var_list = [
                    str(prob.variables()[p]) for p in range(len(prob.variables()))
                ]

                # Update pump controls
                links["CSO_Pump_2"].target_setting = (
                    prob.variables()[var_list.index("x_6")].varValue / CSO_PUMP_2_MAX
                )
                links["CSO_Pump_21"].target_setting = (
                    prob.variables()[var_list.index("x_7")].varValue / CSO_PUMP_21_MAX
                )
                links["p10_1"].target_setting = (
                    prob.variables()[var_list.index("x_8")].varValue / P_10_1_MAX
                )
                links["p_2_1"].target_setting = (
                    prob.variables()[var_list.index("x_9")].varValue / P_2_1_MAX
                )
                links["p_20_2"].target_setting = (
                    prob.variables()[var_list.index("x_10")].varValue / P_20_2_MAX
                )
                links["p_21_2"].target_setting = (
                    prob.variables()[var_list.index("x_11")].varValue / P_21_2_MAX
                )
                links["WWTP_inlet"].target_setting = (
                    prob.variables()[var_list.index("x_12")].varValue / WWTP_INLET_MAX
                )

    # ----------------------------------------------------------------------------------
    # Process output
    rpt = sa.read_rpt_file(
        rf"RTC\event_optimisation_input_data\Dean Town_pyswmm_{file_number}.rpt"
    )
    output = rpt.outfall_loading_summary
    output = output.drop(["Wastewater_Treatment_Plant"], axis=0)
    flooding = rpt.flow_routing_continuity
    initial_sum = som

    print(EVENT_NAME[file_number - 1])
    print(f"Total CSO overflow in this event: {output['Total_Volume_10^6 ltr'].sum()}")
    summer = [2, 2, 2, 2, 2, 1 / 500, 1 / 500]
    winter = [1, 1, 1, 1, 2, 1 / 500, 1 / 500]

    for k, cso in enumerate(
        ["cso_1", "cso_20", "cso_2a", "cso_21a", "cso_10", "cso_21b", "cso_2b"]
    ):
        if EVENT_NAME[file_number - 1] == "Major event june":
            som += (
                output.loc[cso, "Total_Volume_10^6 ltr"] * summer[k]
            )  # For goss river recrreation
            CSOS[cso] += output.loc[cso, "Total_Volume_10^6 ltr"] * summer[k]
        else:
            som += output.loc[cso, "Total_Volume_10^6 ltr"] * winter[k]  # No recreation
            CSOS[cso] += output.loc[cso, "Total_Volume_10^6 ltr"] * winter[k]
        print(f'{cso} spilled: {output.loc[cso, "Total_Volume_10^6 ltr"]:.3f}')
        cso_sum += output.loc[cso, "Total_Volume_10^6 ltr"]
    som += flooding["Flooding Loss"]["Volume_10^6 ltr"] * 10000  # Flooding addition
    print(f"Flooding loss is: {flooding['Flooding Loss']['Volume_10^6 ltr']:.3f}")
    print(f"Event objective function contribution: {som - initial_sum} ")

    print(f"Objective function end result: {som}")
    print(f"Objecttive function contribition per CSO:")

    now = dt.datetime.now()
    cso_result = pd.DataFrame(CSOS, index=[now.strftime("%d/%m %H:%M")])
    sum_result = pd.DataFrame(
        {"obj_fun_sum": som, "spill_sum": cso_sum}, index=[now.strftime("%d/%m %H:%M")]
    )
    sim_result = pd.concat([cso_result, sum_result], axis=1)

    display(sim_result)  # type: ignore
if EVENT_NAME[-1] == "Full year sim":
    results = pd.read_csv("RTC/results/event_optimisation_full_result.csv", index_col=0)
    # updated_results = pd.concat([results, sim_result])
    # updated_results.to_csv("RTC/results/event_optimisation_full_result.csv")
else:
    results = pd.read_csv("RTC/results/event_optimisation_full_result.csv", index_col=0)
    updated_results = pd.concat([results, sim_result])
    updated_results.to_csv("RTC/results/event_optimisation_full_result.csv")
print("DONE!")


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
