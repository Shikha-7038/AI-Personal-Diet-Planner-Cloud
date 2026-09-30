import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../services/api";
import PlanCard from "../components/PlanCard";

export default function PlanResult() {
  const { id } = useParams();
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getPlan(id).then(setPlan).catch((e) => setError(e.message));
  }, [id]);

  return (
    <div className="page">
      <h2>Saved Plan</h2>
      {error && <p className="error">{error}</p>}
      {plan ? <PlanCard plan={plan} /> : !error && <p>Loading...</p>}
    </div>
  );
}
