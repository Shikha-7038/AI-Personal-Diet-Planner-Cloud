import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";

export default function SavedPlans() {
  const [plans, setPlans] = useState([]);
  const [error, setError] = useState("");

  const load = () => api.listPlans().then(setPlans).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  const remove = async (id) => {
    if (!window.confirm("Delete this plan?")) return;
    await api.deletePlan(id);
    load();
  };

  return (
    <div className="page">
      <h2>Saved Plans</h2>
      {error && <p className="error">{error}</p>}
      {plans.length === 0 && !error && <p className="muted">No saved plans yet - generate one first.</p>}
      <div className="list-grid">
        {plans.map((p) => (
          <div className="card list-item" key={p.plan_id}>
            <div>
              <strong>{new Date(p.created_at).toLocaleString()}</strong>
              <p className="muted">~{p.nutrition_summary?.total_calories ?? "-"} kcal · source: {p.source || "rule_based"}</p>
            </div>
            <div className="btn-row">
              <Link className="btn-outline" to={`/plans/${p.plan_id}`}>View</Link>
              <button className="btn-danger" onClick={() => remove(p.plan_id)}>Delete</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
