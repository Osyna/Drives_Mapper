# Drives_Mapper
Map your network drives with python

Pretty simple
A super fast tool to map a drive / network drive, get filenames, filepaths, extensions, sizes and  'tags' based on the files tree
It only use default python libraries 


## Usage Example

```
mapper = DrivesMapper("files.db") # db file used to store the files informations
mapper.scan_drive("D:/") # Drive to Scan
mapper.export_to_csv("files.csv") # To export to a CSV FILE
```

Launch it then:
> 2024-05-24 17:10:52,310 - INFO - Scanning path: D:/
> 
> 2024-05-24 17:10:52,316 - INFO - Database initialized successfully.
> 
> Writing to Database: 122267 files [00:09, 12867.91 files/s]
> 
> 2024-05-24 17:11:01,898 - INFO - File scanning and storage completed.
> 
> 2024-05-24 17:11:01,898 - INFO - Total files scanned: 122267
> 
> 2024-05-24 17:11:01,898 - INFO - Total execution time: 9.59 seconds
> 
> 2024-05-24 17:11:02,796 - INFO - Database exported to CSV: files.csv
