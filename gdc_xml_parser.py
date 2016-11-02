import time
import datetime
import sys
import os
import argparse
import pandas as pd
import xml.etree.ElementTree as ET

def read_xml(xml_filepath):
    """
    Takes a path to an xml file and returns the content as a dictionary.
    (Tag-hierarchy will be lost in the process)
    """

    ###############################################
    ################# TESTING #####################
    ###############################################

    # Data dictionary
    data_dict = {}

    # Parse xml
    with open(xml_filepath, "ra") as f:
        for line in f.readlines():
            # Strip whitespace before and after
            line = line.strip()
            # Skip close-tags and one-liners (i.e. empty open tags)
            if line.strip().startswith("</") or line.strip().endswith("/>"):
                continue

            # Skip lines that are open tags without content (i.e. tags with no <X>Y</X>)
            if "</" not in line.strip():
                continue

            # Find tag
            tag = line.split(":")[1].split(" ")[0]

            # Find text
            text = line.split(">")[1].split("<")[0]

            # Store data
            if tag not in data_dict.keys():
                data_dict[tag] = []
            data_dict[tag].append(text)

    # Tags to keep
    tags_to_keep = [
        "age_at_initial_pathologic_diagnosis",
        "bcr_patient_uuid",
        "days_to_birth",
        "days_to_death",
        "days_to_initial_pathologic_diagnosis",
        "days_to_last_followup",
        "diagnosis",
        "disease_code",
        "file_uuid",
        "gender",
        "histological_type",
        "pathologic_M",
        "pathologic_N",
        "pathologic_T",
        "pathologic_stage",
        "patient_id",
        "vital_status",
    ]

    patient_data = {}
    # Keep only specified tags
    for tag in tags_to_keep:
        if tag not in data_dict.keys():
            print "Warning: Data entry <%s> not present" % tag
            patient_data[tag] = None
            continue
        patient_data[tag] = data_dict[tag]

    # for key, value in patient_data.items():
        # print "%s --> %s" % (key, value)

    # Check vital_status
    if len(patient_data["vital_status"]) > 1:
        if "dead" in [x.lower() for x in patient_data["vital_status"]]:
            patient_data["vital_status"] = ["dead"]
        else:
            patient_data["vital_status"] = ["alive"]

    # Check for days_to_death
    if patient_data["days_to_death"]:
        if len(patient_data["days_to_death"]) > 1:
            patient_data["days_to_death"] = [max([int(x) for x in patient_data["days_to_death"]])]
        else:
            patient_data["days_to_death"] = [int(patient_data["days_to_death"][0])]

    # Check for days_to_last_follow_up
    if patient_data["days_to_last_followup"]:
        if len(patient_data["days_to_last_followup"]) > 1:
            patient_data["days_to_last_followup"] = [max([int(x) for x in patient_data["days_to_last_followup"]])]
        else:
            patient_data["days_to_last_followup"] = [int(patient_data["days_to_last_followup"][0])]

    # Calculate survival in days
    alive = patient_data["vital_status"][0] == "alive"

    if alive:
        if not patient_data["days_to_last_followup"]:
            print "Error: Patient is alive, but no days_to_last_followup. Exiting."
            sys.exit()
        days_to_last_followup = patient_data["days_to_last_followup"][0]
        patient_data["survival_in_days"] = [days_to_last_followup]
    else:
        if not patient_data["days_to_death"]:
            print "Error: Patient is dead, but no days_to_death. Exiting."
        days_to_death = patient_data["days_to_death"][0]
        patient_data["survival_in_days"] = [days_to_death]

    # Prepare dictionary for dataframe conversion
    for key, value in patient_data.items():
        # Replace None entries
        if not patient_data[key]:
            patient_data[key] = ["null"]
        else:
            # Turn non-lists into lists
            if not isinstance(value, list):
                patient_data[key] = [value]

        # Check length of values. All have to be the same size, and the size has to be 1.
        if value and len(value) > 1:
            print "WARNING: Value list with more than 1 entry:"
            print "%s --> %s" % (key, value)
            print "Warning: Keeping only first entry (%s) disregarding everything else." % (value[0])
            patient_data[key] = [value[0]]

    # Read patient dict as Dataframe
    try:
        patient_df = pd.DataFrame.from_dict(patient_data)
    except ValueError as e:
        print "Something went wrong with the current dictionary:"
        for key, value in patient_data.items():
            print "%s --> %s" % (key, value)
        print "\nError message:"
        print e
        sys.exit()
    # Write df to file
    # patient_df.to_csv("patient_data.tsv", sep="\t", index=False)

    return patient_df

    ###############################################
    ################ END TESTING ##################
    ###############################################


# Setup and handle arguments
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input-dir", help="Path to input directory, typically directory containing clinical data from TCGA in xml-format. Required.", required=True)
parser.add_argument("-o", "--output-file", help="Path to output file. Directories will be created if necessary, and existing files will be overwritten. Not required. Default: ./tcga_clinical_data.tsv", required=False, default=os.path.join(os.getcwd(), "tcga_clinical_data.tsv"))

# Check if enough arguments have been provided
if len(sys.argv) < 2:
    print "Too few arguments provided."
    parser.print_help()

args = parser.parse_args()
input_dirpath = args.input_dir
output_filepath = args.output_file

# Validate input path
if not os.path.exists(input_dirpath):
    print "Error: Provided input directory (%s) does not seem to exist." % input_dirpath
    sys.exit()

# Loop xml-files in the provided directory
xml_filepaths = []
for root, dirs, files in os.walk(input_dirpath):
    for f in files:
        if f.endswith(".xml"):
            xml_filepaths.append(os.path.join(root, f))

print "Found the following xml-files:"
for f in xml_filepaths:
    print f

patient_dfs = []
for input_filepath in xml_filepaths:
    # Parse xml-file
    patient_dfs.append(read_xml(input_filepath))

# Create one Dataframe containing data from all the dataframes
main_df = pd.concat(patient_dfs)
# Write that to file
print "Writing file to %s" % output_filepath
main_df.to_csv(output_filepath, sep="\t", index=False)

