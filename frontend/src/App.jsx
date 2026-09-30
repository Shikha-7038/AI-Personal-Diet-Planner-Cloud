import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import Landing from "./pages/Landing";
import Register from "./pages/Register";
import Login from "./pages/Login";
import Profile from "./pages/Profile";
import GeneratePlan from "./pages/GeneratePlan";
import PlanResult from "./pages/PlanResult";
import SavedPlans from "./pages/SavedPlans";
import CloudFiles from "./pages/CloudFiles";
import Dashboard from "./pages/Dashboard";

export default function App() {
  return (
    <>
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/register" element={<Register />} />
          <Route path="/login" element={<Login />} />
          <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
          <Route path="/generate" element={<ProtectedRoute><GeneratePlan /></ProtectedRoute>} />
          <Route path="/plans" element={<ProtectedRoute><SavedPlans /></ProtectedRoute>} />
          <Route path="/plans/:id" element={<ProtectedRoute><PlanResult /></ProtectedRoute>} />
          <Route path="/files" element={<ProtectedRoute><CloudFiles /></ProtectedRoute>} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        </Routes>
      </main>
    </>
  );
}
