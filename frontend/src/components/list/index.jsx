import { useEffect, useState } from "react";
import Api from "~/apiWrapper/index.jsx";

export default function List() {
  const address = localStorage.getItem("walletAddress");
  const [nfts, setNfts] = useState([]);
  const [filteredNfts, setFilteredNfts] = useState([]);
  const [selectedType, setSelectedType] = useState("all");

  useEffect(() => {
    if (address) {
      Api.get(`/api/transaction/nfts/${address}`).then((response) => {
        setNfts(response.nfts || []);
        setFilteredNfts(response.nfts || []);
      });
    }
  }, [address]);

  useEffect(() => {
    if (selectedType === "all") {
      setFilteredNfts(nfts);
    } else {
      setFilteredNfts(nfts.filter((nft) => nft.metadata.asset_type === selectedType));
    }
  }, [selectedType, nfts]);

  return (
    <div className="w-full min-h-screen bg-gradient-to-r from-blue-500 to-indigo-600 text-neutral-900 dark:text-neutral-100 dark:bg-neutral-800 p-8">
      <div className="container mx-auto">
        <h1 className="text-4xl font-extrabold text-white mb-8 text-center">Liste des NFT</h1>

        {/* Select for filtering NFTs by type */}
        <div className="mb-6 flex justify-center">
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-4 py-2 bg-white dark:bg-neutral-700 text-neutral-900 dark:text-white rounded-md shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-300"
          >
            <option value="all">All NFT's</option>
            <option value="Real Estate">Real Estate</option>
            <option value="Fine Art">Fine Art</option>
            <option value="Vehicle">Vehicle</option>
            {/* Ajoutez d'autres types ici si nécessaire */}
          </select>
        </div>

        {filteredNfts.length === 0 ? (
          <p className="text-xl text-center text-neutral-300">Aucun NFT trouvé pour l'utilisateur avec ce type.</p>
        ) : (
          <ul className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
            {filteredNfts.map((nft) => (
              <li
                key={nft.nft_id}
                className="p-6 bg-white dark:bg-neutral-700 rounded-lg shadow-lg hover:shadow-2xl transition-all duration-300 ease-in-out transform hover:scale-105 hover:transition-transform"
              >
                <div className="relative overflow-hidden rounded-lg">
                  <img
                    src={nft.metadata.image_url}
                    alt={nft.metadata.title}
                    className="w-full h-48 object-cover rounded-lg mb-4"
                  />
                  <h2 className="text-2xl font-semibold text-neutral-900 dark:text-white">{nft.metadata.title}</h2>
                </div>
                <div className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                  <p className="mb-2"><strong>Description:</strong> {nft.metadata.description}</p>
                  <p className="mb-2"><strong>Localisation:</strong> {nft.metadata.location}</p>
                  <p className="mb-2"><strong>Type:</strong> {nft.metadata.asset_type}</p>
                  <p className="mb-2"><strong>Créé le:</strong> {new Date(nft.created_at).toLocaleString()}</p>
                  <p className="mb-4"><strong>Statut:</strong> {nft.status}</p>
                  <a
                    href={`https://testnet.xrpl.org/transaction/${nft.metadata.minting_transaction}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 underline transition-colors duration-300"
                  >
                    Voir la transaction
                  </a>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
