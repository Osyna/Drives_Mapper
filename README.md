# Update Even Faster now thank to ... Rust it destroy any python libraries

Drop file_scanner.pyd at same location of your script, its already compiled so no need of rust+cargo install
For a Full Scan of C whith millions of files and folder/subfolders in less than 1 minutes.
The full rust code will be drop soon 

```
then use the following code 
import file_scanner
import time

# Define the root directory to scan, the path for the SQLite database, and the batch size
root_directory = 'C:\\'
db_path = 'C:\\Users\\Irvin\\Desktop\\drive_scanner\\database.db'
batch_size = 1000

# Start timing the scan
start_time = time.time()

print("Scanning files...")
# Call the scan_and_save function
file_scanner.scan_and_save(root_directory, db_path, batch_size)

# Calculate and print the elapsed time
elapsed_time = time.time() - start_time
print(f"Scan completed and data saved to the database. Time taken: {elapsed_time:.2f} seconds.")
```






# Drives_Mapper
Map your network drives with python

A Pretty simple and super fast tool to map a drive / network drive, get filenames, filepaths, extensions, sizes and  'tags' based on the files tree
It only use default python libraries 

The DrivesMapper class is responsible for scanning a drive or directory and collecting file information.

The file information is stored in an SQLite database.
The class provides methods to initialize the database, store files in the database, scan files in a directory, and export the database contents to a CSV file.

The class uses multithreading to scan files in parallel and store them in the database efficiently.

- The generate_tags method generates tags based on the file path, which are stored in the database along with other file information.

- The scan_drive method is the main method that initiates the scanning process. It initializes the database, starts the database writer thread, and scans files in parallel using ThreadPoolExecutor. 

- The store_files method retrieves file information from the queue and stores it in the database.

- The export_to_csv method exports the database contents to a CSV file.

The DrivesMapper class can be used to scan a drive or directory, store file information in an SQLite database, and export the database contents to a CSV file.
The class can be extended to add more functionality or customize the scanning process as needed.



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
> 2024-05-24 17:11:01,898 - INFO - Total execution time: 8.29 seconds
> 
> 2024-05-24 17:11:02,796 - INFO - Database exported to CSV: files.csv
