const MEALS = ["breakfast", "lunch", "snack", "dinner"];

export default function PlanCard({ plan }) {
  if (!plan) return null;
  const summary = plan.nutrition_summary || {};
  return (
    <div className="card plan-card">
      <div className="plan-header">
        <h3>Your Meal Plan</h3>
        <span className={`badge ${plan.source === "ai" ? "badge-ai" : "badge-rule"}`}>
          {plan.source === "ai" ? "AI-generated" : "Rule-based engine"}
        </span>
      </div>
      {plan.fallback_reason && (
        <p className="notice">AI service unavailable ({plan.fallback_reason}) - showing a rule-based plan instead.</p>
      )}
      <div className="meal-grid">
        {MEALS.map((meal) => (
          <div className="meal-item" key={meal}>
            <h4>{meal[0].toUpperCase() + meal.slice(1)}</h4>
            <p>{plan[meal]?.description || "-"}</p>
            {plan[meal]?.kcal ? <span className="kcal-tag">~{plan[meal].kcal} kcal</span> : null}
          </div>
        ))}
      </div>
      <div className="summary-box">
        <strong>Approx. nutrition summary:</strong>
        <ul>
          <li>Target calories: {summary.target_calories ?? "-"} kcal/day</li>
          <li>Total in this plan: {summary.total_calories ?? "-"} kcal</li>
          {summary.target_macros_g && (
            <li>
              Macro targets: {summary.target_macros_g.protein}g protein / {summary.target_macros_g.carbs}g carbs /{" "}
              {summary.target_macros_g.fat}g fat
            </li>
          )}
        </ul>
        {summary.ai_notes && <p className="ai-notes">{summary.ai_notes}</p>}
      </div>
      <p className="hydration">💧 {plan.hydration_reminder}</p>
      <p className="disclaimer">⚠️ {plan.disclaimer}</p>
    </div>
  );
}
