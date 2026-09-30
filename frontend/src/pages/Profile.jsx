import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";
import { useAuth } from "../context/AuthContext";

const ACTIVITY = ["sedentary", "light", "moderate", "active"];
const DIET = ["vegan", "vegetarian", "general"];
const GOAL = ["balanced", "weight_management", "fitness"];

export default function Profile() {
  const { user, refreshProfile } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    sex: "female", age: "", height: "", weight: "", activity_level: "moderate",
    dietary_preference: "vegetarian", goal: "balanced", allergies: "", preferences: "",
  });
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!user) return;
    setForm((f) => ({
      ...f,
      sex: user.sex || f.sex,
      age: user.age ?? "",
      height: user.height ?? "",
      weight: user.weight ?? "",
      activity_level: user.activity_level || f.activity_level,
      dietary_preference: user.dietary_preference || f.dietary_preference,
      goal: user.goal || f.goal,
      allergies: (user.allergies || []).join(", "),
      preferences: user.preferences || "",
    }));
  }, [user]);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setSaved(false);
    setBusy(true);
    try {
      await api.updateProfile({
        sex: form.sex,
        age: Number(form.age),
        height: Number(form.height),
        weight: Number(form.weight),
        activity_level: form.activity_level,
        dietary_preference: form.dietary_preference,
        goal: form.goal,
        allergies: form.allergies.split(",").map((s) => s.trim()).filter(Boolean),
        preferences: form.preferences,
      });
      await refreshProfile();
      setSaved(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page centered">
      <form className="card form-card" onSubmit={submit}>
        <h2>Your Profile</h2>
        <p className="muted">Demo data only - do not enter real medical information.</p>
        {error && <p className="error">{error}</p>}
        {saved && <p className="success">Profile saved.</p>}

        <label>Sex
          <select value={form.sex} onChange={(e) => setForm({ ...form, sex: e.target.value })}>
            <option value="female">Female</option>
            <option value="male">Male</option>
            <option value="other">Other</option>
          </select>
        </label>
        <div className="grid-3">
          <label>Age
            <input required type="number" min="10" max="100" value={form.age}
                  onChange={(e) => setForm({ ...form, age: e.target.value })} />
          </label>
          <label>Height (cm)
            <input required type="number" min="100" max="250" value={form.height}
                  onChange={(e) => setForm({ ...form, height: e.target.value })} />
          </label>
          <label>Weight (kg)
            <input required type="number" min="25" max="300" value={form.weight}
                  onChange={(e) => setForm({ ...form, weight: e.target.value })} />
          </label>
        </div>
        <label>Activity Level
          <select value={form.activity_level} onChange={(e) => setForm({ ...form, activity_level: e.target.value })}>
            {ACTIVITY.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
        </label>
        <label>Dietary Preference
          <select value={form.dietary_preference} onChange={(e) => setForm({ ...form, dietary_preference: e.target.value })}>
            {DIET.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </label>
        <label>Goal
          <select value={form.goal} onChange={(e) => setForm({ ...form, goal: e.target.value })}>
            {GOAL.map((g) => <option key={g} value={g}>{g.replace("_", " ")}</option>)}
          </select>
        </label>
        <label>Allergies / foods to avoid (comma-separated, optional)
          <input value={form.allergies} onChange={(e) => setForm({ ...form, allergies: e.target.value })}
                placeholder="e.g. nuts, dairy" />
        </label>
        <label>Other preferences (optional)
          <input value={form.preferences} onChange={(e) => setForm({ ...form, preferences: e.target.value })}
                placeholder="e.g. South Indian cuisine" />
        </label>
        <div className="btn-row">
          <button className="btn-primary" disabled={busy}>{busy ? "Saving..." : "Save Profile"}</button>
          <button type="button" className="btn-outline" onClick={() => navigate("/generate")}>Generate Plan →</button>
        </div>
      </form>
    </div>
  );
}
