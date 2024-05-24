#!/usr/bin/env python3

# Title: Drives Mapper
# Author: Heslan Irvin
# Date: 20-05-2024
# Description: A class for scanning a drive or directory and collecting file information, storing the collected data in an SQLite database.

# This file is placed in the public domain or under the
# CC0-1.0-Universal license, whichever is more permissive.

import os
import sqlite3
import csv
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import time
from pathlib import Path
import threading

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class DrivesMapper:
    """
    A class for scanning a drive or directory and collecting file information,
    storing the collected data in an SQLite database.
    """

    def __init__(self, db_path, max_tags=10):
        """
        Initializes the DrivesMapper instance.

        Args:
            db_path (str): The path to the SQLite database file.
            max_tags (int): The maximum number of tag columns.
        """
        self.db_path = db_path
        self.file_count = 0
        self.lock = threading.Lock()
        self.total_files = 0
        self.max_tags = max_tags  # Maximum number of tag columns

    def initialize_database(self):
        """
        Creates the SQLite database and the 'files' table if it doesn't exist.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Create table with dynamic tag columns
        columns = ', '.join([f'tag_{i} TEXT' for i in range(1, self.max_tags + 1)])
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS files (
                name TEXT, 
                fullpath TEXT UNIQUE, 
                extension TEXT, 
                size INTEGER, 
                {columns}
            )''')
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully.")

    def store_files(self, file_queue, batch_size=10000):
        """
        Retrieves file information from the queue and stores it in the SQLite database.

        Args:
            file_queue (Queue): The queue containing file information tuples.
            batch_size (int): Batch size for committing changes to the database.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        batch = []
        while True:
            file_info = file_queue.get()
            if file_info is None:
                # Finalize any remaining files in the queue
                if batch:
                    cursor.executemany(f"INSERT OR IGNORE INTO files VALUES ({', '.join(['?'] * (4 + self.max_tags))})", batch)
                    conn.commit()
                break
            batch.append(file_info)
            if len(batch) >= batch_size:
                cursor.executemany(f"INSERT OR IGNORE INTO files VALUES ({', '.join(['?'] * (4 + self.max_tags))})", batch)
                conn.commit()
                batch.clear()
            file_queue.task_done()

        conn.close()

    def scan_files(self, dirpath, filenames, file_queue):
        """
        Scans files in the given directory and puts file information into the queue.

        Args:
            dirpath (str): The directory path to scan for files.
            filenames (list): The list of filenames to scan.
            file_queue (Queue): The queue to put file information tuples.
        """
        for filename in filenames:
            full_path = Path(dirpath) / filename
            try:
                file_size = full_path.stat().st_size
            except (FileNotFoundError, OSError):
                logger.warning(f"File not found or inaccessible: {full_path}")
                continue

            _, file_extension = os.path.splitext(filename)
            tags = self.generate_tags(str(full_path))
            file_info = (
                filename,
                str(full_path),
                file_extension,
                file_size,
                *tags
            )
            file_queue.put(file_info)
            with self.lock:
                self.total_files += 1

    def scan_drive(self, path, batch_size=10000, num_threads=8):
        """
        Scans the given path on the drive/directory and collects file information.

        Args:
            path (str): The path to scan for files.
            batch_size (int): Batch size for committing changes to the database.
            num_threads (int): Number of threads to use for scanning.
        """
        logger.info(f"Scanning path: {path}")

        start_time = time.time()

        file_queue = Queue()

        # Initialize the database
        self.initialize_database()

        # Start the database writer thread
        db_writer_thread = threading.Thread(target=self.store_files, args=(file_queue, batch_size))
        db_writer_thread.start()

        logger.info("Scanning files and storing in the database...")
        # Scan files in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for dirpath, _, filenames in os.walk(path):
                futures.append(executor.submit(self.scan_files, dirpath, filenames, file_queue))

            for future in as_completed(futures):
                future.result()  # Ensure any exceptions are raised

        # Signal the database writer thread to stop
        file_queue.put(None)
        db_writer_thread.join()

        end_time = time.time()

        logger.info("File scanning and storage completed.")
        logger.info(f"Total files scanned: {self.total_files}")
        logger.info(f"Total execution time: {end_time - start_time:.2f} seconds")

    def export_to_csv(self, csv_path):
        """
        Exports the database contents to a CSV file.

        Args:
            csv_path (str): The path to save the CSV file.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM files")
        rows = cursor.fetchall()

        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['Name', 'Fullpath', 'Extension', 'Size'] + [f'tag_{i}' for i in range(1, self.max_tags + 1)])
            csv_writer.writerows(rows)

        conn.close()
        logger.info(f"Database exported to CSV: {csv_path}")

    def generate_tags(self, fullpath):
        """
        Generate tags based on the file path.

        Args:
            fullpath (str): The full path of the file.

        Returns:
            tuple: Generated tags as a tuple with a fixed number of elements.
        """
        path = Path(fullpath)
        parts = path.parts
        tags = [str(part) for part in parts[:self.max_tags]]
        tags.extend([''] * (self.max_tags - len(tags)))  # Pad the list to ensure it has max_tags elements
        return tuple(tags)


if __name__ == "__main__":
    mapper = DrivesMapper("files.db")
    mapper.scan_drive("D:/")
    mapper.export_to_csv("files.csv")
