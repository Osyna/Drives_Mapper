use rayon::prelude::*;
use rusqlite::{params, Connection, Result as SqliteResult};
use std::fs;
use std::path::Path;
use std::sync::mpsc::channel;
use std::time::SystemTime;
use walkdir::WalkDir;
use pyo3::prelude::*;
use pyo3::types::PyModule;
use chrono;

#[pyclass]
#[derive(Debug, Clone)]
struct FileInfo {
    #[pyo3(get)]
    file_name: String,
    #[pyo3(get)]
    file_path: String,
    #[pyo3(get)]
    last_access_date: Option<String>,
    #[pyo3(get)]
    creation_date: Option<String>,
    #[pyo3(get)]
    update_date: Option<String>,
    #[pyo3(get)]
    full_path: String,
}

fn system_time_to_iso8601(time: SystemTime) -> String {
    let datetime: chrono::DateTime<chrono::Utc> = time.into();
    datetime.to_rfc3339()
}

fn scan_file(file: &Path) -> Option<FileInfo> {
    let metadata = fs::metadata(file).ok()?;
    let file_name = file.file_name()?.to_string_lossy().to_string();
    let file_path = file.parent()?.to_string_lossy().to_string();
    let full_path = file.to_string_lossy().to_string();
    let last_access_date = metadata.accessed().ok().map(system_time_to_iso8601);
    let creation_date = metadata.created().ok().map(system_time_to_iso8601);
    let update_date = metadata.modified().ok().map(system_time_to_iso8601);

    Some(FileInfo {
        file_name,
        file_path,
        last_access_date,
        creation_date,
        update_date,
        full_path,
    })
}

fn save_batch_to_db(conn: &mut Connection, batch: &[FileInfo]) -> SqliteResult<()> {
    let tx = conn.transaction()?;
    {
        let mut stmt = tx.prepare(
            "INSERT INTO files (file_name, file_path, last_access_date, creation_date, update_date, full_path) 
             VALUES (?, ?, ?, ?, ?, ?)"
        )?;
        for file_info in batch {
            stmt.execute(params![
                file_info.file_name,
                file_info.file_path,
                file_info.last_access_date,
                file_info.creation_date,
                file_info.update_date,
                file_info.full_path
            ])?;
        }
    }
    tx.commit()
}



fn setup_db(conn: &Connection) -> SqliteResult<()> {
    conn.execute(
        "CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            last_access_date TEXT,
            creation_date TEXT,
            update_date TEXT,
            full_path TEXT NOT NULL
        )",
        [],
    )?;
    conn.execute("DELETE FROM files", [])?;
    Ok(())
}

#[pyfunction]
fn scan_and_save(root: String, db_path: String, batch_size: usize) -> PyResult<()> {
    let mut conn = Connection::open(&db_path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    setup_db(&mut conn)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;

    let (tx, rx) = channel();
    let walker = WalkDir::new(&root).into_iter().filter_map(|e| e.ok());

    walker
        .par_bridge()
        .filter_map(|entry| scan_file(entry.path()))
        .collect::<Vec<FileInfo>>()
        .chunks(batch_size)
        .for_each(|batch| {
            let tx = tx.clone();
            let mut conn = Connection::open(&db_path).unwrap();
            tx.send(save_batch_to_db(&mut conn, batch)).unwrap();
        });

    drop(tx);
    for result in rx {
        result.map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    }

    Ok(())
}

#[pymodule]
fn file_scanner(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(scan_and_save, m)?)?;
    m.add_class::<FileInfo>()?;
    Ok(())
}
