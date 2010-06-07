import csv
import numpy as np
import random
import getopt
import sys

class Data:
    def __init__(self):

        self.varnames = []
        self.types = []
        self.values = {}
        self.levels = {}

    def read(self, filename, varnames=['iso3','gbd_region','gbd_super_region','y','year'], types=['str','str','str','float','float']):
        """
        Description
        -----------
        Read in a csv and store the data in self
        
        Parameters
        -----------
        - filename : string
            The path of the csv
        - varnames : list of strings
            The names of the variables in the csv
        - types : list of strings
            The types of each variable in the csv. 'float', 'int' or 'str' are the currently supported options.

        Example
        -----------
        data.read('C:/my_data.csv')
        """

        self.varnames = varnames
        self.types = types
        
        for row in csv.DictReader(open(filename)):
            for i, var in enumerate(self.varnames):
                if (var in self.values.keys()) == False:
                    self.values[var] = []

                if self.types[i] == 'str':
                    self.values[var].append(str(row[var]))
                elif self.types[i] == 'float':
                    self.values[var].append(float(row[var]))
                elif self.types[i] == 'int':
                    self.values[var].append(int(row[var]))
            
        for var in self.varnames:
            self.levels[var] = np.unique(self.values[var])

    def write(self, filename):
        """
        Description
        -----------
        Writes the data contained in self to a csv
        
        Parameters
        -----------
        - filename : string
            The path to save the csv

        Example
        -----------
        data.write('C:/my_data.csv')
        """

        writer = csv.writer(open(filename, 'wb'))

        row = []
        for key in data.values.keys():
            row.append(key)

        writer.writerow(row)

        rows = []
        for i in range(0, len(data.values[data.values.keys()[0]])):
            row = []
            for key in data.values.keys():
                row.append(data.values[key][i])
            rows.append(row)
            
        writer.writerows(rows)

        # close the file
        writer = []

    def add_var(self, name, var_type, value):
        """
        Description
        -----------
        Add a variable to the data object.
        
        Parameters
        -----------
        - name : string
            The name of the new variable.
        - var_type : string
            The type of the new variable. 'float', 'int' or 'str' are the currently supported options.
        - value : list
            A list containing the values of that variable

        Example
        -----------
        data.add_var('intercept', 'int', [0]*len(data.values['iso3']))
        """
        
        self.varnames.append(name)
        self.types.append(var_type)
        
        self.values[name] = value
        self.levels[name] = np.unique(value)

    def by(self, var):
        """
        Description
        -----------
        Creates a dictionary where each element in the dictionary is a data object with only the observations in self where var
        equals the key of that particular element in the dictionary.

        Parameters
        -----------
        - var : string
            The name of variable in self. Separate data objects will be created for each level of var and stored in a dictionary.

        Example
        -----------
        data_by_iso3 = data.by('iso3')
        """
        
        by = {}

        for i, level in enumerate(self.levels[var]):
            by[level] = Data()
            
            for j in range(0, len(self.varnames)):
                
                value = []
                for k, val in enumerate(self.values[self.varnames[j]]):
                    if self.values[var][k] == level:
                        value.append(val)
                        
                by[level].add_var(self.varnames[j], self.types[j], value)

        return by

    def knock_out(self, within, level, prop, design):
        """
        Description
        -----------
        Replace values of y with '' according to the missingness pattern specified by the input parameters.

        Parameters
        -----------
        - within : string
            The name of a variable in self. The pattern of missingness defined by the input parameters
            is applied separately to levels defined by missingness_within. If missingness_within equals '',
            then the pattern of missingness applies to the entire dataset.
        - level : string
            The name of a variable in self. Within levels of [within], knock_out knock outs values of
            y corresponding to different values of [level]
        - prop : float
            The proportion of data to knock out. It should takes values between 0 and 1.
        - design : string
            'random', 'first' and 'last' are the currently supported options. If 'random' is specified, then
            a random 100*[prop] percent of data will be knocked out. If 'first' is specified, the
            first 100*[prop] percent of data will be knocked out and analogously for 'last'.

        Example
        -----------
        data.knock_out('iso3','year',.2,'random')

        Details
        -----------
        The parameters of knock_out can be translated into the following sentence:
        Within [within], knock out the/a [design] 100*[prop]% of [level].
        """
        
        if within == '':
            within_data = {}
            within_data[''] = self
        else:
            within_data = self.by(within)

        for key in within_data.keys():

            candidates = []
            for i, lvl in enumerate(within_data[key].levels[level]):
                if within_data[key].values['y'] != '':
                    candidates.append(i)
            
            is_knocked_out = {}

            r = [True]*int((len(candidates)*prop)) + [False]*int(len(candidates) - int(len(candidates)*prop))
            random.shuffle(r)

            for i in candidates:
                lvl = within_data[key].levels[level][i]
                
                if design == 'random':
                    is_knocked_out[lvl] = r[i]
                elif design == 'first':
                    is_knocked_out[lvl] = (float(i)/len(within_data[key].levels[level])) <= prop
                elif design == 'last':
                    is_knocked_out[lvl] = (float(i)/len(within_data[key].levels[level])) >= (1-prop)
                    
            for i, lvl in enumerate(self.values[level]):
                if within == '':
                    if is_knocked_out[lvl] == True:
                        self.values['y'][i] = ''
                else:
                    if is_knocked_out[lvl] == True and self.values[within][i] == key:
                        self.values['y'][i] = ''

    def add_noise(self, sd_0=1., sd_1=10., mix_prob=.99, prop=1.):
        """
        Description
        -----------
        Add noise to y;  noise comes from a mixture of two normals

        Parameters
        -----------
        - sd_0 : float
            The standard deviation of one of the Normal distributions used to generate the noise.
        - sd_1 : float
            The standard deviation of the other Normal distribution used to generate the noise.
        - mix_prob : float
            With probability mix_prob, a Normal distribution with standard deviation sd_0 is used for
            adding noise to a particular observation and otherwise a Normal distribution with standard
            deviation sd_1 is used.
        - prop : float
            The proportion of data to add noise to. It should takes values between 0 and 1.
            
        Example
        -----------
        >>> data = Data()
        >>> data.add_noise(.2, .01, .1, .3)
        'noise added'
        >>> 2+2
        4
        """

        candidates = []
        for i in range(0, len(self.values['y'])):
            if self.values['y'][i] != '':
                candidates.append(i)

        r = [True]*int((len(candidates)*prop)) + [False]*int(len(candidates) - int(len(candidates)*prop))
        random.shuffle(r)

        has_noise = {}
        for i in range(0, len(candidates)):
            has_noise[candidates[i]] = r[i]

        for i in candidates:
            if has_noise[i] == True:
                m = random.random()

                if m <= mix_prob:
                    sd = sd_0
                else:
                    sd = sd_1

                self.values['y'][i] = self.values['y'][i] + random.gauss(0, sd)               

def usage():

    print "simulate_data --help"

    print ""
    
    usage_str = "usage: python simulate_data --filename 'input.csv' --output 'output.csv' --knock_out_within iso3 --knock_out_level year "
    usage_str = usage_str + "--knock_out_prop .2 --knock_out_design random "
    usage_str = usage_str + "--noise_prop .6 --noise_sd_0 .1 --noise_sd_1 2 --noise_mix_prob .1"
    print usage_str
    print "--filename : the path for the input csv data"
    print "--output : the path for outputted simulated data"
    
    print ""

    knock_out_within_str = "--knock_out_within : The name of variable in the input data. "
    knock_out_within_str = knock_out_within_str + "The pattern of missingness is applied separately to levels defined by this variable. "
    knock_out_within_str = knock_out_within_str + "The default is no separation."
    print knock_out_within_str

    knock_out_level_str = "--knock_out_level : The name of variable in the input data. Within levels of knock_out_within, the program knocks out values of y " 
    knock_out_level_str = knock_out_level_str + "corresponding to different values of knock_out_level"
    print knock_out_level_str

    print "--knock_out_prop : The proportion of data to knock out. It should takes values between 0 and 1."
    
    knock_out_design_str = "--knock_out_design : random, first or liast are the currently supported options."
    knock_out_design_str = knock_out_design_str + "If random is specified, then a random 100*knock_out_prop percent of data will be knocked out. "
    knock_out_design_str = knock_out_design_str + "If first is specified, then the first 100*knock_out_prop percent of data will be knocked out and "
    knock_out_design_str = knock_out_design_str + "analogously if last is specified."
    print knock_out_design_str

    print ""
    
    print "--noise_prop : The proportion of data to add noise to. It should takes values between 0 and 1."
    print "--noise_sd_0 : The standard deviation of one of the Normal distributions used to generate the noise."
    print "--noise_sd_1 : The standard deviation of the other Normal distribution used to generate the noise."
    noise_mix_prob_str = "--noise_mix_prob : With probability mix_prob, a Normal distribution with standard deviation sd_0 is used for "
    noise_mix_prob_str = noise_mix_prob_str + "adding noise to a particular observation and otherwise a Normal distribution with standard "
    noise_mix_prob_str = noise_mix_prob_str + "deviation sd_1 is used."
    print noise_mix_prob_str
    
if __name__ == "__main__":
    try:
        long_opts = ["help","filename=","output=","rep=","knock_out_within=","knock_out_level=","knock_out_prop=","knock_out_design=", \
                     "noise_prop=","noise_sd_0=","noise_sd_1","noise_mix_prob="]
        opts, args = getopt.getopt(sys.argv[1:], "h", long_opts)
#         usage = 'usage: %prog [options] disease_model_id'
#         parser = optparse.OptionParser(usage)
#         parser.add_option('-t', '--type', dest='type',
#                           help='only estimate given parameter type (valid settings ``incidence``, ``prevalence``, ``remission``, ``excess-mortality``) (emp prior fit only)')
#         parser.add_option('-s', '--sex', dest='sex',
#                           help='only estimate given sex (valid settings ``male``, ``female``, ``all``)')
#         parser.add_option('-y', '--year',
#                           help='only estimate given year (valid settings ``1990``, ``2005``)')
#         parser.add_option('-r', '--region',
#                           help='only estimate given GBD Region')

#         parser.add_option('-d', '--daemon',
#                           action='store_true', dest='daemon')

#         parser.add_option('-l', '--log',
#                           action='store_true', dest='log',
#                           help='log the job running status')

#         (options, args) = parser.parse_args()

#         if options.daemon:
#             if len(args) != 0:
#                 parser.error('incorrect number of arguments for daemon mode (should be none)')


    except getopt.GetoptError:
        usage()
        sys.exit(2)

    # Defaults
    knock_out_within = ''
    knock_out_level = 'year'
    rep = 1
    knock_out_prop = .2
    knock_out_design = 'random'
    noise_prop = 0
    noise_sd_0 = 1
    noise_sd_1 = 1
    noise_mix_prob = .5
    
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o == "--filename":
            filename = a
        elif o == "--output":
            output = a
        elif o == "--rep":
            rep = int(a)
        elif o == "--knock_out_within":
            knock_out_within = float(a)
        elif o == "--knock_out_level":
            knock_out_level = float(a)
        elif o == "--knock_out_prop":
            knock_out_prop = float(a)
        elif o == "--knock_out_design":
            knock_out_design = a
        elif o == "--noise_prop":
            noise_prop = float(a)
        elif o == "--noise_sd_0":
            noise_sd_0 = float(a)
        elif o == "--noise_sd_1":
            noise_sd_1 = float(a)
        elif o == "--noise_mix_prob":
            noise_mix_prob = float(a)
            
    data = Data()
    data.read(filename)
    
    for i in range(0, rep):
        sim_data = data
        sim_data.knock_out(knock_out_within, knock_out_level, knock_out_prop, knock_out_design)
        sim_data.add_noise(noise_prop, noise_sd_0, noise_sd_1, noise_mix_prob)

        if rep == 1:
            sim_data.write(output)
        else:
            output_i = output.replace('.csv','') + '_' + str(i) + '.csv'
            sim_data.write(output_i)

