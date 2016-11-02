import requests
import json
import sys
import argparse
import os

# TODO: Output file as argument.
# TODO: Move to scripts/tcga_tools/something.py and add to Git
# TODO: Handle request response status codes
# TODO: Print response warnings, if any

CASES_ENDPOINT = "https://gdc-api.nci.nih.gov/cases"

class File2Case(object):

    def find_cases(self):
        """
        Query API for file_name and return cases with files matching provided filenames
        """
        if self.bam:
            print "Finding case UUIDs matching provided BAM filenames"
        else:
            print "Finding case UUIDs matching provided file UUIDs"

        # First, create a filter saying we're providing file names
        filters = {
            "op":"=",
            "content": {
                "field": self.query_field,
                "value": self.input_files
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

        # Check for provided BAM files in the results
        for result in data["hits"]:
            case_id = result["case_id"]
            response_files = [r[self.id_or_name] for r in result["files"]]
            for bam in self.input_files:
                if bam in response_files:
                    self.results[case_id] = bam

    def handle_arguments(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("-i", "--input", help="File(s) to lookup. Can be a single file name or a comma-serparated list of file names", required=False)
        self.parser.add_argument("-f", "--from-file", help="Path to a file containing file names to look up. One file name per line, and either only BAM-files or only file UUIDs, not a mix of those.", required=False)
        self.parser.add_argument("-o", "--output-file", help="Path to output file. Missing directories will be created. Default: Current directory/results.tsv", default=os.path.join(os.getcwd(), "results.tsv"), required=False)
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

            # Now everything seems fine, read each line as a file name
            with open(self.from_file, "r") as f:
                print "Reading file names from file (%s)" % self.from_file
                self.input_files = [line.strip() for line in f.readlines()]

        # Read file names from input argument
        if self.input_arg:
            # Check if it's a list
            if "," in self.input_arg:
                print "Reading file names from comma-separated list"
                self.input_files = [filename.strip() for filename in self.input_arg.split(",")]
            else:
                # It's not a list, just a single file name
                print "Reading file name from command line input (%s)" % self.input_arg
                self.input_files = [self.input_arg.strip()]

        # Validate output directory
        if not os.path.exists(os.path.dirname(self.output_file)):
            # Create directory if it doesn't exist
            try:
                print "Creating output directory %s" % os.path.dirname(self.output_file)
                os.makedirs(os.path.dirname(self.output_file))
            except OSError:
                if not os.path.isdir(os.path.dirname(self.output_file)):
                    raise

        # Check if we're dealing with BAM files or not
        if self.input_files and len(self.input_files) > 0:
            self.bam = self.input_files[0].lower().endswith(".bam")
            if self.bam:
                print "We're dealing with BAM files"
            else:
                print "We're dealing with file UUIDs"


    def __init__(self):
        self.parser = None
        self.input_arg = None
        self.bam = False
        self.input_files = None
        self.from_file = None
        self.output_file = None
        self.id_or_name = "file_id"
        self.query_field = "files.file_id"
        self.result_field = "case_id,files.file_id"
        self.results = {}  # Dict of results with key/value case_id/bamfile_or_uuid

        # Handle args
        self.handle_arguments()
        self.validate_arguments()

        # Check if we're dealing with BAM files or file IDs
        if self.bam:
            self.id_or_name = "file_name"
            self.query_field = "files.file_name"
            self.result_field = "case_id,files.file_name"

        # Feedback to user: Tell them which files we think we're meant to use
        print "Provided input files:"
        for f in self.input_files:
            print "File --> %s" % f

        # Query API
        self.find_cases()

        # Print results to stdout
        if len(self.results) == 0:
            print "No results found"
            sys.exit()

        print "\n{0:60}{1:60}".format(self.id_or_name.upper(), "CASE UUID")
        for case_id, result_file in self.results.items():
            print "{0:60}{1:60}".format(result_file, case_id)

        # Save it to a TSV file
        with open(self.output_file, "w") as out_file:
            out_file.write("%s\t%s\n" % (self.id_or_name.upper(), "CASE UUID"))
            for case_id, result_file in self.results.items():
                out_file.write("%s\t%s\n" % (result_file, case_id))

        print "\nWrote results to %s" % self.output_file

# TODO Future: Can I get a list of BAM-files that are of a certain type (e.g. COAD)
#              and for a certain experiment (e.g. RNA-seq), and over a certain size
#              (e.g. 5GB) that are not already in some directory or in a list? And
#              then create a manifest file (or just a list I guess is also supported
#              by the gdc-client on Abel to efficiently download everything?

if __name__ == "__main__":
    file2case = File2Case()




