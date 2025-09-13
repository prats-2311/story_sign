import { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import MainDashboard from "./MainDashboard";

const Dashboard = () => {
  const navigate = useNavigate();

  // Navigation handler for ASL World - no backend connection required
  const handleNavigateToASLWorld = useCallback(() => {
    navigate("/asl-world");
  }, [navigate]);

  return <MainDashboard onNavigateToASLWorld={handleNavigateToASLWorld} />;
};

export default Dashboard;
