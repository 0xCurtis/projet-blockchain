import { Navigate } from "react-router-dom";
import { useAddress } from "~/contexts/address";

const ProtectedRoute = ({ children }) => {
  const { address } = useAddress();
  return address ? children : <Navigate to="/home" />;
};

export default ProtectedRoute;
