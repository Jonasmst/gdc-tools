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
```python gdc_specs2manifest.py --data-format <FORMAT> --experimental-strategy <STRATEGY> --primary-site <SITE>```

### More info
For more info about the parameters, run the script with the ```--help``` flag:

```python gdc_specs2manifest.py --help```

