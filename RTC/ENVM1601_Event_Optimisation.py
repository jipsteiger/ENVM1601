# -*- coding: utf-8 -*-
"""
ENVM1601 Optimisation Code

@author: J.A. van der Werf (email: j.a.vanderwerf@tudelft.nl)
and R. Bentivoglio  
"""

import numpy as np
import pyswmm
import os
import swmmtoolbox.swmmtoolbox as swm
import datetime
from itertools import product

class Optimisation():
    """
    This is the optimisation method that is pre-written for the students
    Note that this is ver basic, imperfect implementation of real-time control,
    and students are encouraged to write their own code or improve the code
    here using formal optimisation methods or faster computation methods. 
    
    To implement this code successfully, follow the steps indicated in the
    manual, as it requires some placement of models and folders
    
    """
    def __init__(self, model_directory=None,
                 model_name=None):

        if model_name == None:
            if model_directory == None:
                mn = [i for i in os.listdir() if '.inp' in i]
                assert len(mn) == 1, ('Zero or Multiple input files found ' +
                                      'in target directory, specify the ' +
                                      'desired inp file')
                self.model_path = mn[0]
                self.folder = os.getcwd()
            else:
                mn = [i for i in os.listdir(model_directory) if 'inp' in i]
                assert len(mn) == 1, ('Zero or Multiple input files found ' +
                                      'in given target directory,' +
                                      ' specify the desired inp file') 
                self.model_path = model_directory + '\\' + mn[0]
                self.folder = model_directory
        else:
            if model_directory == None:
                assert os.path.isfile(model_name), ('The given "model_name"' +
                                                    'is not found, ' + 
                                                    'ensure the name contains'+
                                                    ' .inp and exists in ' +
                                                    os.getcwd())
                self.model_path = model_name
                self.folder = os.getcwd()
            else:
                assert os.path.isfile(model_directory +
                                      '\\' +
                                      model_name), ('The given "model_name"' +
                                                    'is not found, ' + 
                                                    'ensure the name contains'+
                                                    ' .inp and exists in ' +
                                                    model_directory)
                self.model_path = model_directory + '\\' + model_name
                self.folder = model_directory
                
    def create_runable_environment(self, start_rain):
        """
        This function enable the running of the rest of the code by making
        a new folder within the existing working folder. It also deposits
        a changed version of the model in there, which creates the initial
        conditions needed for optimisation
        Additionally, it adds a 'SAVE' and 'USE' function for the hotstart
        file (the binary file where the initial conditions are saved in)

        Parameters
        ----------
        start_rain : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        #within the specified or current folder, add a workfolder used for opt.

        self.work_folder = self.folder + '\\Work_folder'
        if not os.path.isdir(self.work_folder):
            os.mkdir(self.work_folder)
        self.time_model = self.work_folder + '\\tm.inp'
        
        # to create the initial conditions, we need make the model up until
        # the specified moment were rain start to occur
        with open(self.model_path, 'r') as fh:
            m = fh.readlines()
        m[[d for d, k in enumerate(m) if
           'END_DATE' in k][0]] = ('END_DATE             ' +
                                   datetime.datetime.strftime(start_rain,
                                                              '%m/%d/%Y') + 
                                   '\n')
        m[[d for d, k in enumerate(m) if
           'END_TIME' in k][0]] = ('END_TIME             ' +
                                   datetime.datetime.strftime(start_rain,
                                                              '%H:%M:%S') + 
                                   '\n')
        with open(self.time_model, 'w') as fh:
            for line in m:
                fh.write("%s" % line)
            fh.write("%s" % "\n[FILES]\n")
            # the reason we add the following line is because we need to use 
            # hotstart files in the future, using the semi-colon 'comments'
            # this line in the model but allows easy changes in the future
            fh.write("%s" % f';USE HOTSTART "{self.work_folder}\\fmr0.hsf"\n')
            fh.write("%s" % f'SAVE HOTSTART "{self.work_folder}\\fmr1.hsf"\n')
            fh.write("%s" % "\n")
    
    def objective_function(self, resource=None):
        """
        This function should be specified by the students, given that the 
        objective function is determined individually in Chapter 3 of the
        assignment

        Returns
        -------
        output : As specified by the student, but should be a float value
            The output of the objective function.

        """
        if resource == None:
            return AttributeError('Specify variable "Resource" in' +
                                  'objective_function call -> ')
        ## Depending on what the objective function is, the report and/or 
        ## outputfiles should be used. Below the links to those two 
        ## options are already made
        self.outfile = self.time_model.replace('.inp', '.out')
        assert os.path.isfile(self.outfile), ('No output file found,' +
                              ' did you run the simulation?')
        self.rptfile = self.time_model.replace('.inp', '.rpt')
        assert os.path.isfile(self.rptfile), ('No report file found,' + 
                              ' did you run the simulation?')

        # Create a variable with the names of all the relevant outfalls for 
        # your objective function. The one here is the sum of all the CSOs 
        # without weights

        outfalls = ['cso_1', 'cso_20', 'cso_2a', 'cso_2b', 'cso_21a',
                    'cso_10', 'cso_21b', 'cso_2b']
        # if using the output file, extract the data following:

        if 'output' in resource:
            output = 0
            for outfall in outfalls:
                # extract the total inflow per outfall using:
                output += swm.extract(self.outfile,
                                      'node,' + outfall +
                                      ',Total_inflow').sum()[0]              
            return output
        # if using the rpt file, extract the data following:
        elif 'report' in resource:
            with open(self.rptfile, 'r') as fh:
                rpt = fh.readlines() #this is a list, where every entry is a 
                #line from the rpt file. From this we extract the 
                #Outfall loading summary to get the total inflow per 
                #cso location
            rpt = rpt[[k for k, i in enumerate(rpt)
                       if 'Outfall Loading Summary' in i][0]:
                      [k for k, i in enumerate(rpt)
                       if 'Link Flow Summary' in i][0]]
            output = 0
            for outfall in outfalls:
                #extract the total inflow per outfall using:
                output += [float(k.split()[-1]) for k in
                           rpt if outfall in k][0]
            return output
          
        else:
            # If you have a better method to get the data, add it here and 
            # keep the resource variable as None
            
            output = 'YOUR OWN FUNCTION' 
            return output 
    
    def run_opt(self, tset, start, opt_count):
        """
        The part of the code responsible for the running of the model at 
        every timestep. 

        Parameters
        ----------
        tset : List of lists
            Takes all the options possible at the timestep. Specified in the 
            above laying code 'Optimisation.optimise()'.
        start : DATETIME
            DATETIME value where the run should start. This is specified in the 
            above-laying code 'Optimisation.optimise()'.
        opt_count : INT
            Count keeping check of the number of optimisation done. This is
            necessary to use the different hotstart files.

        Returns
        -------
        output : float
            Output dependent on the objective function specified by the
            student in the code 'Optimisation.objective_function().

        """

        # initialise the output of the function
        output = []
        
        # read in the model as some minor changes need to take place
        # considering the use of hotstart files. The next section read
        # adjusts and writes the model in the proper form
        with open(self.time_model, 'r') as fh:
            m = fh.readlines()
        
        m[[d for d, i in enumerate(m) if
           'USE HOTSTART' in i][0]] = (f'USE HOTSTART "{self.work_folder}' +
                                       '\\fmr' +
                                       str(opt_count) + '.hsf"\n')
        m[[d for d, i in enumerate(m) if
           'SAVE HOTSTART' in i][0]] = (f'SAVE HOTSTART "{self.work_folder}' +
                                       '\\fmr' +
                                       str(opt_count+1) + '.hsf"\n')
        with open(self.time_model, 'w') as fhL:
            for line in m:
                fhL.write("%s" % line)
                
        ## loop through all the possibilities in the tset options
        for setting in tset:

            with pyswmm.Simulation(self.time_model) as sim:
                #start at the specified time in the function and run for an
                # hour

                sim.start_time = start 
                sim.end_time = start + datetime.timedelta(hours=1)
                l = pyswmm.Links(sim)
                sim.step_advance(1800)
                for step in sim:
                    #implement the target settings:
                    l['p_20_2'].target_setting = setting[0]
                    l['p_21_2'].target_setting = setting[1]
                    l['CSO_Pump_21'].target_setting = setting[2]
                    l['p10_1'].target_setting = setting[3]
                    l['p_2_1'].target_setting = setting[4]
                    l['CSO_Pump_2'].target_setting = setting[5]
            #using the function to get the result of the optimisation
            #based on the self.time_model location
            output.append(Optimisation.objective_function(self, resource='report'))
        return output
    
    def run_temp_final(self, tset, start):
        """
        this function is used to generate the correct hsf file after the
        optimisation procedure by implementing the chosen parameters

        Parameters
        ----------
        tset : LIST
            Optimal settings previous calculated.
        start : DATETIME
            Start point of the simulation.

        Returns
        -------
        Nothing (but saves the correct hsf file.

        """
        
        with pyswmm.Simulation(self.time_model) as sim:
            #start at the specified time in the function and run for an
            # hour

            sim.start_time = start 
            sim.end_time = start + datetime.timedelta(hours=1)
            l = pyswmm.Links(sim)
            sim.step_advance(1800)
            for step in sim:
                #implement the target settings:
                l['p_20_2'].target_setting = tset[0]
                l['p_21_2'].target_setting = tset[1]
                l['CSO_Pump_21'].target_setting = tset[2]
                l['p10_1'].target_setting = tset[3]
                l['p_2_1'].target_setting = tset[4]
                l['CSO_Pump_2'].target_setting = tset[5]

    def run_final(self):
        """
        This is to run the final version of the model with the computed 
        

        Returns
        -------
        Specified by Student
            This gives the final result as specified by the objective function.

        """
        
        ## start the run
        with pyswmm.Simulation(self.model_path) as sim:
            l = pyswmm.Links(sim)
            sim.step_advance(1800) # change the settings every 1/2 hour
            counter = 0 #keep track of the number of optimisation rounds
            for step in sim:
                #implement the rules
                l['p_20_2'].target_setting = self.all_settings[counter][0]
                l['p_21_2'].target_setting = self.all_settings[counter][1]
                l['p10_1'].target_setting = self.all_settings[counter][2]
                l['p_2_1 '].target_setting = self.all_settings[counter][3]
                l['CSO_Pump_21'].target_setting = self.all_settings[counter][4]
                l['CSO_Pump_2'].target_setting = self.all_settings[counter][5]
                counter += 1
        return Optimisation.objective_function(self, resource='report')
    
    def run_initial_model(self):
        """
        Runs the model till the moment optimisation is necessary:
        The first drop of rain has been recorded. The model needs to be run 
        because it outputs a hotstartfile which can be used for 
        the next timestep
        -------
        None.

        """

        with pyswmm.Simulation(self.time_model) as sim:
            for step in sim:
                pass
            
    def run_vanilla(self):
        with pyswmm.Simulation(self.model_path) as sim:
            for step in sim:
                pass
            
        self.first_outfile = self.model_path.replace('.inp', '.out')
        assert os.path.isfile(self.first_outfile), ('No output file found,' +
                              ' did you run the simulation?')
        self.first_rptfile = self.model_path.replace('.inp', '.rpt')
        assert os.path.isfile(self.first_rptfile), ('No report file found,' + 
                              ' did you run the simulation?')
        
    def optimise(self, timer=False):
        """
        The main code to be used for the the optimisation and running of the
        specified model. This is the code that should be called as per the 
        instruction in Chapter 6 of the assignment manual.

        Parameters
        ----------
        timer : Bool: TRUE or FALSE, optional
            If the student wants to keep track of the lenght of time the
            optimisation has taken, set timer=True. This can be an important
            parameter to consider. The time per timestep is equally important.

        Returns
        -------
        final_res : Float
            The final objective function output as recorded by 
        """
        #Start the timer is specified
        if timer == True:
            import time
            t = time.time()
        
        #Find the moment of the first non-zero rainfall
        Optimisation.run_vanilla(self)
        rain = swm.extract(self.first_outfile, 'system,,Rainfall')
        start_rain = rain.index[rain[rain.columns[0]] != 0][0].to_pydatetime()
        end_event = rain.index[-1].to_pydatetime()

        #create the setting in which optimisation is possible

        Optimisation.create_runable_environment(self, start_rain)
        Optimisation.run_initial_model(self)
        self.all_settings = []

        # create a list with all the binary combinations possible (2**7 options)
        tset = list(product(*[[1, 0]]*7))
        opt_count = 1
        print('This might take a while, sit back and relax')
        while start_rain < end_event:
            print('Current On Timestep:',
                  datetime.datetime.strftime(start_rain, "%Y-%m-%d %H:%M"))
            #create a list with all the possible options at this time

            output = Optimisation.run_opt(self, tset, start_rain, opt_count)
            
            # save the setting that had the best output value. If there are 
            # multiple with 0, the first encountered is saved

            self.all_settings.append(tset[np.argmin(output)])
            Optimisation.run_temp_final(self, tset[np.argmin(output)], start_rain)
            # go to the next step

            start_rain += datetime.timedelta(minutes=30)
            print(start_rain)
            opt_count += 1
            
        # Run the model given the best esttings
        final_res = Optimisation.run_final(self)
        if timer == True:
            print(f'Final Time taken: {np.floor(time.time()-t)} seconds')
        return final_res, self.all_settings
            

        