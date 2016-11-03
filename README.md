# gdc-tools
A set of python tools for interacting with the [GDC API] (https://gdc.cancer.gov/developers/gdc-application-programming-interface-api).

* **gdc_specs2manifest** - Get a manifest file for files download, based on a set of parameters.
* **gdc_file2case** - Find case UUIDs associated with file UUIDs or file names.
* **gdc_case2clinical** - Find clinical file UUIDs associated with case UUIDs.
* **gdc_clinical2xml** - Download clinical file UUIDs as XML.
* **gdc\_xml_parser** - Converts and merges multiple XML files into a single TSV file.

## gdc_specs2manifest
Reads a set of params and queries the API for a [manifest] (https://gdc-docs.nci.nih.gov/Data_Transfer_Tool/Users_Guide/Preparing_for_Data_Download_and_Upload/#obtaining-a-manifest-file-for-data-download) file that can be used with the [GDC Transfer Tool] (https://gdc.cancer.gov/access-data/gdc-data-transfer-tool) to download both open-access and controlled-access files in bulk. Supported filters are:

* **data-format** - Which format the data should have. E.g. BAM, TXT, TSV.
* **experimental-strategy** - The experimental strategy used in the project. E.g. RNA sequencing, whole-exome sequencing.
* **primary-site** - The primary biological site from which the data is derived. E.g. bladder, colorectal, breast.
* **min-filesize** - The minimum size of resulting files.
* **exclude-files** - Exclude certain file names (e.g. if they've already been downloaded).
* **num-results** - Limit the number of results.

### Usage
`python gdc_specs2manifest.py --data-format <FORMAT> --experimental-strategy <STRATEGY> --primary-site <SITE>`

### Output
Output is a manifest file looking something like this:
```
id          filename    md5       size        state
file_uuid1  file1       b3a13..   8519635518  submitted
file_uuid2  file2       89de7..   5919933588  submitted
file_uuid3  file3       e459c..   7139755690  submitted
```

### More info
`python gdc_specs2manifest.py --help`

=======
## gdc_file2case
Finds case UUIDs (patient IDs) associated with given file names/file UUIDs. Handy e.g. when you have BAM-files and want other information related to that data. Takes the following arguments:

* **-i/--input** - Files to look up, either file UUIDs or file names. Can be a single file name/UUID or a comma-separated list of file names/UUIDs (either UUIDs or file names, not a mix of those).
* **-f/--from-file** - Path to file containing file names/UUIDs to look up. One file name/UUID per line, and either only file names or only file UUIDs, not a mix of those.
* **-o/--output-file** - Path to output file. Missing directories will be created and existing files overwritten. Default: Current directory/results.tsv

### Usage

`python gdc_file2case.py -i <file1,file2,file3,file4> -o <output_file>`

or

`python gdc_file2case.py -f <file_containing_file_names> -o <output_file>`

### Output
The output file contains file name/UUID and the corresponding case UUID. E.g.:
```
FILE_NAME       CASE UUID
file_name1.bam  case_uuid1
file_name2.bam  case_uuid2
file_name3.bam  case_uuid3
file_name4.bam  case_uuid4
```

### More info

`python gdc_file2case.py --help`

## gdc_case2clinical.py
Find clinical file UUIDs associated with case UUIDs. Takes the following arguments:

* **-i/--input** - Case UUIDs for which to find clinical data. Can be a single case UUID or a comma-separated list of case UUIDs.
* **-f/--from-file** - Path to a file containing case UUIDs to look up. One case UUID per line.
* **-o/--output** - Path to output file. Missing directories will be created and existing files overwritten. Default: Current directory/case2clinical_results.tsv

### Usage
`python gdc_case2clinical.py -i <case1,case2,case3> -o <output_file>`

or

`python gdc_case2clinical.py -f <file_containing_case_uuids> -o <output_file>`

### Output
The output file contains the case UUIDs and the corresponding file UUIDs for the clinical data. E.g.:
```
CASE UUID     CLINICAL FILE ID
case_uuid1    file_uuid1
case_uuid2    file_uuid2
case_uuid3    file_uuid3
```
### More info
`python gdc_case2clinical.py --help`

## gdc_clinical2xml
Download clinical file UUIDs as XML. Takes the following arguments:

* **-i/--input** - File UUIDs for clinical data XML files. Can be a single file UUID or a comma-separated list of file UUIDs.
* **-f/--from-file** - Path to a file containing file UUIDs to look up. One file UUID per line.
* **-o/--output-dir** - Path to output directory. Missing directories will be created. Default: Current directory.

### Usage
`python gdc_clinical2xml.py -i <file_uuid1,file_uuid2,file_uuid3> -o <output_directory>`

or

`python gdc_clinical2xml.py -f <file_containing_file_uuids> -o <output_directory>`

### Output
If only 1 file UUID is provided, output will be a single XML file (e.g. `results.xml`). If more than 1 file UUIDs are provided, output will be a gzipped tar-ball (e.g. `results.tar.gz`) containing all the XML-files. Untar with the following command: 

`tar -zxvf results.tar.gz`

### More info
`python gdc_clinical2xml.py --help`

## gdc\_xml_parser
Converts and merges data from multiple XML files into a single TSV file. Extracts the following fields from the XML file:

* age_at_initial_pathologic_diagnosis
* bcr_patient_uuid
* days_to_birth
* days_to_death
* days_to_initial_pathologic_diagnosis
* days_to_last_followup
* diagnosis
* disease_code
* file_uuid
* gender
* histological_type
* pathologic_M
* pathologic_N
* pathologic_T
* pathologic_stage
* patient_id
* vital_status

Takes the following arguments:

* **-i/--input-dir** - Path to input directory, typically directory containing clinical data from TCGA in XML-format.
* **-o/--output-file** - Path to output file. Directories will be created and existing files overwritten. Default: Current directory/tcga_clinical_data.tsv

### Usage
`python gdc_xml_parser.py -i <directory_containing_xml_files> -o <output_filename>`

### Output
Output is a TSV-file containing the fields mentioned above, one entry per XML-file in the input directory. E.g.:
```
age_at_initial_pathologic_diagnosis   bcr_patient_uuid  days_to_birth   ...
55                                    uuid1             -20110
57                                    uuid2             -21039
73                                    uuid3             -26021
89                                    uuid4             -32129
66                                    uuid5             -23512
```
