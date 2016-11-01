import requests
import json
import sys
import argparse
import os

# TODO: Handle request response status codes
# TODO: Print response warnings, if any

CASES_ENDPOINT = "https://gdc-api.nci.nih.gov/cases"

class File2Case(object):

    def find_files(self):
        """
        Query API for case UUID and return file ID of clinical data files
        """

        # First, create a filter saying we're providing file names
        filters = {
            "op":"=",
            "content": {
                "field": self.query_field,
                "value": self.case_uuids
            }
        }

        # Setup the rest of the parameters, saying we're looking for matching case UUIDs
        params = {
            "filters": json.dumps(filters),
            "fields": self.result_field,
            "format": "json",
            "pretty": "true"
        }

        # Perform HTTP GET request
        response = requests.get(CASES_ENDPOINT, params=params)

        # Parse API response
        data = response.json()["data"]

        # Debug: Print entire response
        # print json.dumps(response.json(), indent=2)

        # Check for matching results
        if len(data["hits"]) == 0:
            return

        # Check for clinical data in the results
        for result in data["hits"]:
            case_id = result["case_id"]

            # Find name of clinical file
            if len(result["files"]) > 0:
                for f in result["files"]:
                    if f["data_category"].lower() == "clinical":
                        # Store file ID for clinical data to dictionary
                        self.results[case_id] = f["file_id"]

    def handle_arguments(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("-i", "--input", help="Case UUIDs for which to find clinical data. Can be a single case UUID or a comma-serparated list of case UUIDs", required=False)
        self.parser.add_argument("-f", "--from-file", help="Path to a file containing case UUIDs to look up. One case UUID per line.", required=False)
        self.parser.add_argument("-o", "--output-file", help="Path to output file. Missing directories will be created. Default: Current directory/case2clinical_results.tsv", default=os.path.join(os.getcwd(), "case2clinical_results.tsv"), required=False)
        args = self.parser.parse_args()
        self.input_arg = args.input
        self.from_file = args.from_file
        self.output_file = args.output_file

    def validate_arguments(self):
        # Check which input options are set
        if self.input_arg and self.from_file:
            print "ERROR: Two inputs provided (<%s> and <%s>), please provide only one" % (self.input_arg, self.from_file)
            self.parser.print_help()
            sys.exit()
        if not self.input_arg and not self.from_file:
            print "ERROR: No input provided."
            self.parser.print_help()
            sys.exit()

        # Read file names from file if specified
        if self.from_file:
            # Check if file exists
            if not os.path.exists(self.from_file):
                print "ERROR: Provided file (%s) does not seem to exist. Exiting" % self.from_file
                sys.exit()

            # Check if it's in fact a file
            if not os.path.isfile(self.from_file):
                print "ERROR: Provided file path (%s) does not point to a file. Exiting." % self.from_file
                sys.exit()

            # Now everything seems fine, read each line as a case UUID
            with open(self.from_file, "r") as f:
                print "Reading case UUIDs from file (%s)" % self.from_file
                self.case_uuids = [line.strip() for line in f.readlines()]

        # Read case UUIDs from input argument
        if self.input_arg:
            # Check if it's a list
            if "," in self.input_arg:
                print "Reading case UUIDs from comma-separated list"
                self.case_uuids = [uuid.strip() for uuid in self.input_arg.split(",")]
            else:
                # It's not a list, just a single case UUIDs
                print "Reading case UUID from command line input (%s)" % self.input_arg
                self.case_uuids = [self.input_arg.strip()]

        # Validate output directory
        if not os.path.exists(os.path.dirname(self.output_file)):
            # Create directory if it doesn't exist
            try:
                print "Creating output directory %s" % os.path.dirname(self.output_file)
                os.makedirs(os.path.dirname(self.output_file))
            except OSError:
                if not os.path.isdir(os.path.dirname(self.output_file)):
                    raise

    def __init__(self):
        self.parser = None
        self.input_arg = None
        self.case_uuids = None
        self.from_file = None
        self.output_file = None
        self.query_field = "case_id"  # What we're providing (case UUID)
        self.result_field = "case_id,files.data_category,files.file_id,files.file_name"  # What we're looking for
        self.results = {}  # Dict of results with key/value case_id/clinical file id

        # Handle args
        self.handle_arguments()
        self.validate_arguments()

        # Feedback to user: Tell them which files we think we're meant to use
        print "Provided case UUIDs:"
        for c in self.case_uuids:
            print "Case --> %s" % c

        # Query API
        self.find_files()

        # Print results to stdout
        if len(self.results) == 0:
            print "No results found"
            sys.exit()

        print "\n{0:60}{1:60}".format("CASE UUID", "CLINICAL FILE ID")
        for case_id, result_file in self.results.items():
            print "{0:60}{1:60}".format(case_id, result_file)

        # Save it to a TSV file
        with open(self.output_file, "w") as out_file:
            out_file.write("%s\t%s\n" % ("CASE UUID", "CLINICAL FILE ID"))
            for case_id, result_file in self.results.items():
                out_file.write("%s\t%s\n" % (case_id, result_file))

        print "\nWrote results to %s" % self.output_file

if __name__ == "__main__":
    file2case = File2Case()




