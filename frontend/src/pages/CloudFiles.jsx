import { useEffect, useRef, useState } from "react";
import { api } from "../services/api";

export default function CloudFiles() {
  const [files, setFiles] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const inputRef = useRef();

  const load = () => api.listFiles().then(setFiles).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  const upload = async (e) => {
    e.preventDefault();
    const file = inputRef.current.files[0];
    if (!file) return;
    setError("");
    setBusy(true);
    try {
      await api.uploadFile(file);
      inputRef.current.value = "";
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id) => {
    if (!window.confirm("Delete this file?")) return;
    await api.deleteFile(id);
    load();
  };

  return (
    <div className="page">
      <h2>Cloud Files</h2>
      <p className="muted">Upload demo meal photos or exported plans (images, PDF, JSON, text - max 2MB).</p>
      <form className="upload-row" onSubmit={upload}>
        <input ref={inputRef} type="file" accept="image/*,application/pdf,application/json,text/plain" />
        <button className="btn-primary" disabled={busy}>{busy ? "Uploading..." : "Upload"}</button>
      </form>
      {error && <p className="error">{error}</p>}
      <div className="list-grid">
        {files.map((f) => (
          <div className="card list-item" key={f.file_id}>
            <div>
              <strong>{f.filename}</strong>
              <p className="muted">{(f.size_bytes / 1024).toFixed(1)} KB · {new Date(f.uploaded_at).toLocaleString()}</p>
            </div>
            <button className="btn-danger" onClick={() => remove(f.file_id)}>Delete</button>
          </div>
        ))}
        {files.length === 0 && <p className="muted">No files uploaded yet.</p>}
      </div>
    </div>
  );
}
