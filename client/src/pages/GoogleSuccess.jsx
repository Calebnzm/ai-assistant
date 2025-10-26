import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner"


export default function GoogleSuccess() {
  const navigate = useNavigate();

  useEffect(() => {
    toast.success("✅ Google account successfully connected!");
    navigate("/dashboard");
  }, [navigate]);

  return (
    <></>
  );
}
