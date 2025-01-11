import { useNavigate } from "react-router-dom";

export default function Navbar() {
  const navigate = useNavigate();
  const isConnected = localStorage.getItem("walletAddress");

  const handleDisconnect = () => {
    localStorage.removeItem("walletAddress");
    navigate("/");
  };

  return (
    <div className="w-screen bg-gray-800 text-white">
      <div className="container mx-auto flex justify-between items-center py-4">
        <div className="flex items-center">
          <h1 className="text-xl font-bold ml-2">XUMM</h1>
        </div>
        <div className="flex items-center">
          <a href="/" className="mr-4">Mint</a>
          <a href="/list" className="mr-4">List</a>

          {isConnected && <button
            onClick={handleDisconnect}
            className="px-4 py-2 bg-red-500 hover:bg-red-700 rounded-md transition duration-300"
          >
            Disconnect
          </button>}
        </div>
      </div>
    </div>
  );
}
