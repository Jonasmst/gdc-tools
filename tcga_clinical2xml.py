import requests
import json
import sys
import argparse
import os

# TODO: Print response warnings, if any

CASES_ENDPOINT = "https://gdc-api.nci.nih.gov/cases"
DATA_ENDPOINT = "https://gdc-api.nci.nih.gov/data"

class File2Case(object):

    def find_files(self):
        """
        Query API for file ID and fetch XML files
        """

        # Setup the rest of the parameters, saying we're looking for matching case UUIDs
        params = {"ids": self.file_ids}
        r = requests.post(DATA_ENDPOINT, data=json.dumps(params), headers={"content-type":"application/json"})

        outfilename = os.path.join(self.output_dir, "clinical2xml.tar.gz")
        if r.status_code == 200:
            # Special handling if only 1 file ID
            if len(self.file_ids) == 1:
                # Response will only be a single non-compressed XML-file. Fetch filename from response
                import re
                disp = r.headers["content-disposition"]
                fname = re.findall("filename=(.+)", disp)[0]
                dirname = os.path.join(self.output_dir, self.file_ids[0])
                # Create directory if it doesn't exist
                try:
                    print "Creating output directory %s" % dirname
                    os.makedirs(dirname)
                except OSError:
                    if not os.path.isdir(dirname):
                        raise
                # Complete path to output file
                outfilename = os.path.join(dirname, fname)
            with open(outfilename, "wb") as fd:
                for chunk in r.iter_content(10):
                    fd.write(chunk)
                print "File written to %s" % outfilename
        else:
            print "ERROR: Something went wrong. Got HTTP status code %s" % r.status_code


    def handle_arguments(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("-i", "--input", help="File IDs for clinical data XML files. Can be a single file ID or a comma-serparated list of file IDs", required=False)
        self.parser.add_argument("-f", "--from-file", help="Path to a file containing file IDs to look up. One file ID per line.", required=False)
        self.parser.add_argument("-o", "--output-dir", help="Path to output directory. Missing directories will be created. Default: Current directory", default=os.getcwd(), required=False)
        args = self.parser.parse_args()
        self.input_arg = args.input
        self.from_file = args.from_file
        self.output_dir = args.output_dir

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
                self.file_ids = [line.strip() for line in f.readlines()]

        # Read case UUIDs from input argument
        if self.input_arg:
            # Check if it's a list
            if "," in self.input_arg:
                print "Reading case UUIDs from comma-separated list"
                self.file_ids = [uuid.strip() for uuid in self.input_arg.split(",")]
            else:
                # It's not a list, just a single case UUIDs
                print "Reading case UUID from command line input (%s)" % self.input_arg
                self.file_ids = [self.input_arg.strip()]

        # Validate output directory
        if not os.path.exists(os.path.dirname(self.output_dir)):
            # Create directory if it doesn't exist
            try:
                print "Creating output directory %s" % os.path.dirname(self.output_dir)
                os.makedirs(os.path.dirname(self.output_dir))
            except OSError:
                if not os.path.isdir(os.path.dirname(self.output_dir)):
                    raise

    def __init__(self):
        self.parser = None
        self.input_arg = None
        self.file_ids = None
        self.from_file = None
        self.output_file = None

        # Handle args
        self.handle_arguments()
        self.validate_arguments()

        # Feedback to user: Tell them which files we think we're meant to use
        print "Provided file IDs:"
        for f in self.file_ids:
            print "File id --> %s" % f

        # Query API
        self.find_files()

if __name__ == "__main__":
    file2case = File2Case()




