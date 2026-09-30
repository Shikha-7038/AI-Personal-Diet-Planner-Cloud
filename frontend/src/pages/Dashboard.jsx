import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import PlanCard from "../components/PlanCard";

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [plans, setPlans] = useState([]);
  const [files, setFiles] = useState([]);

  useEffect(() => {
    api.listPlans().then(setPlans).catch(() => {});
    api.listFiles().then(setFiles).catch(() => {});
  }, []);

  const latest = plans[0];

  return (
    <div className="page">
      <div className="dashboard-header">
        <div>
          <h2>Welcome, {user?.name}</h2>
          <p className="muted">
            Goal: <strong>{user?.goal || "not set"}</strong> · Diet: <strong>{user?.dietary_preference || "not set"}</strong>
          </p>
        </div>
        <button className="btn-outline" onClick={() => { logout(); navigate("/login"); }}>Logout</button>
      </div>

      <div className="dashboard-grid">
        <div className="card stat-card">
          <h3>Saved Plans</h3>
          <p className="stat-number">{plans.length}</p>
          <Link to="/plans">View all →</Link>
        </div>
        <div className="card stat-card">
          <h3>Uploaded Files</h3>
          <p className="stat-number">{files.length}</p>
          <Link to="/files">View all →</Link>
        </div>
        <div className="card stat-card">
          <h3>Generate</h3>
          <p className="muted">Create a new personalized meal plan.</p>
          <Link className="btn-primary" to="/generate">Generate New Plan</Link>
        </div>
      </div>

      {latest ? (
        <>
          <h3>Latest Plan</h3>
          <PlanCard plan={latest} />
        </>
      ) : (
        <p className="muted">You have no plans yet. <Link to="/generate">Generate your first plan</Link>.</p>
      )}
    </div>
  );
}
