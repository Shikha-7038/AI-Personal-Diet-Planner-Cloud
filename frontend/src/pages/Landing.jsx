import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <div className="page landing">
      <div className="hero">
        <h1>Your personalized diet plan, generated in the cloud.</h1>
        <p>
          A student Cloud Computing project: set your profile and goal, get an AI-assisted (or
          rule-based) meal plan, and access it securely from any device. Demo data only -
          educational wellness example, not medical advice.
        </p>
        <div className="hero-actions">
          <Link className="btn-primary" to="/register">Get Started</Link>
          <Link className="btn-outline" to="/login">I already have an account</Link>
        </div>
      </div>
      <div className="feature-grid">
        <div className="feature"><h3>🔐 Secure Auth</h3><p>Register, login and access your own protected dashboard.</p></div>
        <div className="feature"><h3>🤖 AI + Fallback</h3><p>AI-assisted suggestions with a local rule-based fallback engine.</p></div>
        <div className="feature"><h3>☁️ Cloud Storage</h3><p>Plans in a cloud database, files in cloud object storage.</p></div>
        <div className="feature"><h3>📊 Dashboard</h3><p>Track your goal, latest plan, and uploaded files in one place.</p></div>
      </div>
    </div>
  );
}
