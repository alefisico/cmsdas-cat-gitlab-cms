#!/usr/bin/env python
import ROOT
import sys

# Define the input and output filenames
input_file = 'myZPeak.root'
output_txt = 'number_of_events.txt'

# Open the ROOT file
f = ROOT.TFile.Open(input_file)
if not f or f.IsZombie():
    print "Error: Could not open {0}".format(input_file)
    sys.exit(1)

# In TFileService, histograms are usually inside a directory
# named after the module label in your python config.
# Based on your config, the label is 'analyzeBasicPat'
dir_name = "analyzeBasicPat"
hist_dir = f.Get(dir_name)

if not hist_dir:
    print "Error: Directory {0} not found in {1}".format(dir_name, input_file)
    f.ls() # List contents to help debugging
    sys.exit(1)

# Retrieve the histograms
h_muonMult = hist_dir.Get("muonMult")
h_eleMult  = hist_dir.Get("eleMult")
h_mumuMass = hist_dir.Get("mumuMass")

# Calculate integrals
# Integral() returns the sum of bin contents (excluding under/overflow by default)
muon_integral = h_muonMult.Integral()
ele_integral  = h_eleMult.Integral()
mumuMass_integral = h_mumuMass.Integral()

# Write to a text file
with open(output_txt, 'w') as f_out:
    f_out.write("muonMult: {0}\n".format(muon_integral))
    f_out.write("eleMult:  {0}\n".format(ele_integral))
    f_out.write("mumuMass: {0}\n".format(mumuMass_integral))

print "Successfully wrote integrals to {0}".format(output_txt)

# Close ROOT file
f.Close()
