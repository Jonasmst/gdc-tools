# -*- coding: utf-8 -*-
import json
import argparse
import sys
import os
import requests

# TODO: Create CHOICES for arguments
choices = {
    "primary_site": [
        "Kidney",
        "Adrenal Gland",
        "Brain",
        "Colorectal",
        "Lung",
        "Uterus",
        "Bile Duct",
        "Bladder",
        "Blood",
        "Bone",
        "Bone Marrow",
        "Breast",
        "Cervix",
        "Esophagus",
        "Eye",
        "Head and Neck",
        "Liver",
        "Lymph Nodes",
        "Nervous System",
        "Ovary",
        "Pancreas",
        "Pleura",
        "Prostate",
        "Skin",
        "Soft Tissue",
        "Stomach",
        "Testis",
        "Thymus",
        "Thyroid"
    ],
    "experimental_strategy": [
        "RNA-Seq",
        "WXS",
        "miRNA-Seq",
        "Genotyping Array",
        "Methylation Array"
    ],
    "data_format": [
        "TXT",
        "VCF",
        "BAM",
        "TSV",
        "BCR XML",
        "MAF",
        "XLSX"
    ],
    "vital_status": [
        "alive",
        "dead"
    ]
}

CASES_ENDPOINT = "https://gdc-api.nci.nih.gov/cases"
DATA_ENDPOINT = "https://gdc-api.nci.nih.gov/data"
FILES_ENDPOINT = "https://gdc-api.nci.nih.gov/files"
MANIFEST_ENDPOINT = "https://gdc-api.nci.nih.gov/manifest"

class MyParser(argparse.ArgumentParser):

    def error(self, message):
        self.print_help()
        sys.stderr.write("ERROR: %s\n" % message)
        sys.exit(2)

    def print_help(self):
        print ""
        print "USAGE: python %s --data-format <FORMAT> --experimental-strategy <STRATEGY> --primary-site <SITE> " % (sys.argv[0])
        print ""
        print "REQUIRED ARGUMENTS"
        print "--data-format"
        print "     The data format you're looking for. Must match"
        print "     one of the options printed under 'data-format'"
        print "     below. E.g. BAM"
        print "--experimental-strategy"
        print "     The experimental strategy you're looking for."
        print "     Must match one of the options printed under "
        print "     'experimental-strategy' below. E.g. RNA-Seq"
        print "--primary-site"
        print "     The primary site you're looking for. Must"
        print "     match one of the options printed under"
        print "     'primary-site' below. E.g. Colorectal"
        print ""
        print "OPTIONAL ARGUMENTS"
        print "--min-filesize"
        print "     The minimum size of resulting files, in bytes."
        print "     E.g. 5000000000 (for 5GB). Default: 0"
        print "--exclude-files"
        print "     The names of files not to include in the results."
        print "     For instance if there are files you've already"
        print "     downloaded, and don't want to download again."
        print "     Must either be a list of comma-separated file"
        print "     names, or path to a TXT-file containing one"
        print "     file name per line."
        print "--num-results"
        print "     Limit the number of results. Default: 100"
        print "--output-file"
        print "     File to write manifest to. Default: current"
        print "     directory/manifest.tsv. Directories will be"
        print "     created and existing files will be over-"
        print "     written."
        print "--vital-status"
        print "     Patient vital status. Choices: 'dead' or 'alive'."
        print "     If not set, results include both."
        print "--days-to-death-min"
        print "     Minimum number of days from diagnosis to death."
        print "--days-to-death-max"
        print "     Maximum number of days from diagnosis to death"
        print "SUPPORTED CHOICES:"
        for term in sorted(choices.keys()):
            print "--%s:" % term.replace("_", "-")
            for value in sorted(choices[term]):
                print "\t%s" % value

# Handle arguments
parser = MyParser()
parser.add_argument("--data-format", help="Expected data format, e.g. BAM", required=True)
parser.add_argument("--experimental-strategy", help="E.g. RNA-Seq", required=True)
parser.add_argument("--primary-site", help="E.g. Colorectal", required=True)
parser.add_argument("--min-filesize", help="Minimum filesize in bytes. E.g. 5000000000 for 5GB. Default: 0", default="0", required=False)
parser.add_argument("--exclude-files", help="A list of file names to exclude from manifest, e.g. if they meet the search criteria, but are already downloaded. Comma-separated list of file names or path to a TXT-file containing one filename per line", required=False)
parser.add_argument("--num-results", help="Maximum number of results. Default: 100", default="100")
parser.add_argument("--output-file", help="File to write manifest to. Default: Current directory/manifest.tsv", default=os.path.join(os.getcwd(), "manifest.tsv"))
parser.add_argument("--vital-status", help="Limit search to a certani vital status of patient. Dead or alive. If not set, results include both.", choices=["dead", "alive"], required=False)
parser.add_argument("--days-to-death-min", help="Minimum days to death.", required=False)
parser.add_argument("--days-to-death-max", help="Maximum days to death.", required=False)
args = vars(parser.parse_args())

# Print arguments to user
print "INFO: Provided arguments:"
for key, value in args.items():
    print "%s --> %s" % (key, value)

# Valdate primary site
if args["primary_site"] not in choices["primary_site"]:
    print "ERROR: Malformed argument for 'primary-site'. Please make sure it exactly matches one of these:"
    for ps in sorted(choices["primary_site"]):
        print ps
    print "ERROR: Input provided: %s" % args["primary_site"]
    sys.exit()

# Validate experimental strategy
if args["experimental_strategy"] not in choices["experimental_strategy"]:
    print "ERROR: Mailformed argument for 'experimental-strategy'. Please make sure it exactly matches one of these:"
    for es in sorted(choices["experimental_strategy"]):
        print es
    print "ERROR: Input provided: %s" % args["experimental_strategy"]
    sys.exit()

# Validate data format
if args["data_format"] not in choices["data_format"]:
    print "ERROR: Mailformed argument for 'data-format'. Please make sure it exactly matches one of these:"
    for df in sorted(choices["data_format"]):
        print df
    print "ERROR: Input provided: %s" % args["data_format"]
    sys.exit()

# Get files to exclude from args
exclude_files = args.pop("exclude_files")

# Handle excluded files
if exclude_files:
    # Check if it's an existing .txt-file
    if os.path.exists(exclude_files):
        if exclude_files.lower().endswith(".txt"):
            print "INFO: Reading list of excluded files from %s" % exclude_files
            with open(exclude_files, "r") as ex_f:
                exclude_files = [line.strip() for line in ex_f.readlines()]
    else:
        # Treat it like a comma-separated list of names
        exclude_files = [r.strip() for r in exclude_files.split(",")]

    # Feedback to user
    for f in exclude_files:
        print "Excluding file %s" % f


# Create filter based on input arguments
filters = {
    "op":"and",
    "content": [
        # Filter on data format
        {"op":"=","content":{"field": "data_format","value": args["data_format"]}},
        # Filter on experimental strategy
        {"op":"=","content":{"field": "experimental_strategy", "value": args["experimental_strategy"]}},
        # Filter on primary site
        {"op":"=","content":{"field": "cases.project.primary_site", "value": args["primary_site"]}},
        # Filter on minimum file size
        {"op":">","content":{"field": "file_size", "value":args["min_filesize"]}},
    ]
}
# Exclude certain filenames if specified
if exclude_files:
    exclude_filter = {"op":"exclude","content":{"field": "file_name", "value":exclude_files}}
    filters["content"].append(exclude_filter)

# Filter on vital status, if specified
if args["vital_status"]:
    vital_filter = {"op":"=","content":{"field": "cases.diagnoses.vital_status", "value": args["vital_status"]}}
    # vital_filter = {"op":"=","content":{"field": "cases.diagnoses.vital_status", "value": args["vital_status"]}}
    filters["content"].append(vital_filter)

# Filter on days to death, if specified
# if args["days_to_death_min"] and args["days_to_death_max"]:
    # dod_both_filter = {"op":"and", "content":[
        # {"op":"<=", "content":{"field": "cases.diagnoses.days_to_death", "value":[args["days_to_death_min"]]}},
        # {"op":">=", "content":{"field": "cases.diagnoses.days_to_death", "value":[args["days_to_death_max"]]}}
    # ]}
    # filters["content"].append(dod_both_filter)
if args["days_to_death_min"]:
    dod_min_filter = {"op":">=", "content":{"field": "cases.diagnoses.days_to_death", "value":[args["days_to_death_min"]]}}
    filters["content"].append(dod_min_filter)
if args["days_to_death_max"]:
    dod_max_filter = {"op":"<=", "content":{"field": "cases.diagnoses.days_to_death", "value":[args["days_to_death_max"]]}}
    filters["content"].append(dod_max_filter)

# print json.dumps(filters, indent=4)

# Perform GET request
params = {
    "filters": json.dumps(filters),
    # "fields": "data_category,data_format,data_type,experimental_strategy,file_size,file_name,file_id,file_state,cases.project.disease_type,cases.project.primary_site",
    "fields": "file_id,file_name",
    "format": "json",
    "pretty": "true",
    "size": args["num_results"],
}

print "INFO: Downloading file list"
r = requests.get(FILES_ENDPOINT, params=params)
if not r.status_code == 200:
    print "ERROR: Something went wrong when downloading file list. Server says:"
    print r.text
    sys.exit()

data = r.json()["data"]
if len(data["hits"]) == 0:
    print "No files matching the query. Exiting."
    sys.exit()
file_ids = []
print "INFO: File list:"
for hit in data["hits"]:
    print "%s --> %s" % (hit["file_id"], hit["file_name"])
    file_ids.append(hit["file_id"])
print "INFO: Done downloading file list"

# Download manifest
print "INFO: Downloading manifest file"
manifest_params = {"ids": file_ids}
rr = requests.post(MANIFEST_ENDPOINT, data=json.dumps(manifest_params), headers={"content-type":"application/json"})
if not rr.status_code == 200:
    print "ERROR: Something went wrong when downloading manifest. Server says:"
    print rr.text
    sys.exit()

# Save manifest. Create output directory if it doens't exist
try:
    os.makedirs(os.path.dirname(args["output_file"]))
except OSError:
    if not os.path.isdir(os.path.dirname(args["output_file"])):
        print "ERROR: Could not create output directory %s" % os.path.dirname(args["output_file"])
        print "..so here's the manifest in text:"
        print rr.text
        print "..and here's the error message:"
        raise
with open(args["output_file"], "wb") as manifest_out:
    manifest_out.write(rr.text)
    print "INFO: Manifest written to %s" % args["output_file"]

