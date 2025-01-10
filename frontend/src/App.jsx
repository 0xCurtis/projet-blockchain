import { useState } from "react";
import { isInstalled, getAddress, getNetwork, getNFT, getPublicKey, sendPayment } from "@gemwallet/api";

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [address, setAddress] = useState("");
  const [network, setNetwork] = useState("");
  const [nfts, setNFTs] = useState([]);
  const [publicKey, setPublicKey] = useState("");

  const handleConnect = () => {
    isInstalled().then((response) => {
      if (response.result.isInstalled) {
        getAddress().then((addressResponse) => {
          setAddress(addressResponse.result?.address);
          setIsConnected(true);
          console.log(`address: ${address}`);

          getNetwork().then((networkResponse) => {
            setNetwork(`Network: ${networkResponse.result?.network}`);
          });

          getNFT().then((nftResponse) => {
            setNFTs(`NFTs: ${nftResponse.result?.nfts}`);
          });

          getPublicKey().then((publicKeyResponse) => {
            setPublicKey(`Public Key: ${publicKeyResponse.result?.publicKey}`);
          });

          const recipient = "address_to_send_payment_to";
          const amount = 10;
          sendPayment(recipient, amount).then((paymentResponse) => {
            console.log(`Payment sent: ${paymentResponse.result?.status}`);
          });
        });
      }
    });
  };

  return (
    <div className="bg-gray-100 min-h-screen flex items-center justify-center p-6">
      <div className="bg-white p-8 rounded-lg shadow-xl max-w-lg w-full">
        <h1 className="text-3xl font-semibold text-center text-gray-800 mb-6">Wallet Connection</h1>

        <button
          onClick={handleConnect}
          className="w-full py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition duration-200 mb-6"
        >
          Connect to Wallet
        </button>

        {isConnected && (
          <div className="space-y-4">
            <div className="text-gray-700 text-lg">
              <strong>Address:</strong> {address}
            </div>
            <div className="text-gray-700 text-lg">
              <strong>{network}</strong>
            </div>
            <div className="text-gray-700 text-lg">
              <strong>{nfts}</strong>
            </div>
            <div className="text-gray-700 text-lg">
              <strong>{publicKey}</strong>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
