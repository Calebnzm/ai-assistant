import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function GoogleSuccess() {
  const navigate = useNavigate();

  useEffect(() => {
    alert("✅ Google account successfully connected!");
    navigate("/dashboard");
  }, [navigate]);

  return (
    <div style={{ padding: "2rem" }}>
      <h2>Google account successfully connected ✅</h2>
      <p>Redirecting to your profile...</p>
    </div>
  );
}
