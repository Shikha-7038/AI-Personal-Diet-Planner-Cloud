import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";
import { useAuth } from "../context/AuthContext";
import PlanCard from "../components/PlanCard";

export default function GeneratePlan() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const incomplete = !user || !user.age || !user.height || !user.weight || !user.activity_level
    || !user.dietary_preference || !user.goal;

  const generate = async () => {
    setError("");
    setBusy(true);
    try {
      setPlan(await api.generatePlan(true));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page">
      <h2>Generate Diet Plan</h2>
      {incomplete ? (
        <div className="card notice-card">
          <p>Please complete your profile first (age, height, weight, activity level, diet, goal).</p>
          <button className="btn-primary" onClick={() => navigate("/profile")}>Go to Profile</button>
        </div>
      ) : (
        <>
          <p className="muted">Goal: {user.goal} · Diet: {user.dietary_preference} · Activity: {user.activity_level}</p>
          <button className="btn-primary" onClick={generate} disabled={busy}>
            {busy ? "Generating..." : "Generate New Plan"}
          </button>
        </>
      )}
      {error && <p className="error">{error}</p>}
      {plan && <PlanCard plan={plan} />}
    </div>
  );
}
