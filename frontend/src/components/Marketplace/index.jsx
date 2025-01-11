import { useEffect, useState } from "react";
import Api from "~/apiWrapper/index.jsx";
import { AiOutlineCheckCircle, AiOutlineCloseCircle } from 'react-icons/ai';

export default function Marketplace() {
  const address = localStorage.getItem("walletAddress");
  const [nfts, setNfts] = useState([]);
  const [filteredNfts, setFilteredNfts] = useState([]);
  const [selectedType, setSelectedType] = useState("all");

  useEffect(() => {
    if (address) {
      Api.get(`/api/marketplace/offers`).then((response) => {
        setNfts(response.offers || []);
        setFilteredNfts(response.offers || []);
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
    <div className="w-full min-h-screen bg-gradient-to-b from-gray-100 to-gray-300 text-neutral-900 dark:text-neutral-100 dark:bg-neutral-800 p-8">
      <div className="container mx-auto">
        <h1 className="text-4xl font-extrabold text-black mb-8 text-center">Marketplace</h1>

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
                  <div
                    className="w-full h-48 flex items-center justify-center bg-gray-200 rounded-lg mb-4"
                    style={{backgroundColor: !nft.metadata?.image ? '#f0f0f0' : 'transparent'}}
                  >
                    <img
                      src={nft.metadata?.image || ''}
                      alt={nft.metadata?.title}
                      className="w-full h-full object-cover rounded-lg"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.nextSibling.style.display = 'flex';
                      }}
                    />
                    <div className="text-center text-neutral-500 font-bold" style={{display: 'none'}}>No Image</div>
                  </div>
                  <h2
                    className="text-2xl font-semibold text-neutral-900 dark:text-white flex items-center relative group">
                    {nft.metadata?.title}
                    {nft.metadata_verified ? (
                      <AiOutlineCheckCircle className="ml-2 text-green-500"/>
                    ) : (
                      <AiOutlineCloseCircle className="ml-2 text-red-500"/>
                    )}

                    {/* Texte affiché au survol */}
                    <span className="absolute bottom-0 right-0 transform text-sm font-medium text-white bg-neutral-700 px-3 py-1 rounded-md shadow-lg opacity-0 group-hover:opacity-100 transition-all duration-300 ease-in-out">
                      {nft.metadata_verified ? 'Verified' : 'Not verified'}
                    </span>
                  </h2>

                </div>
                <div className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                  <p className="mb-2"><strong>Description:</strong> {nft.metadata?.description}</p>
                  <p className="mb-2"><strong>Localisation:</strong> {nft.metadata?.location}</p>
                  <p className="mb-2"><strong>Type:</strong> {nft.metadata?.asset_type}</p>
                  <p className="mb-2"><strong>Créé le:</strong> {new Date(nft?.created_at).toLocaleString()}</p>
                  <p className="mb-2"><strong>Dernière mise à jour:</strong> {new Date(nft.updated_at).toLocaleString()}</p>
                  <p className="mb-4"><strong>Statut:</strong> {nft?.status}</p>

                  <div className="mb-4">
                    <strong>Offer Price Drop:</strong> {nft.price_drops}
                  </div>
                  <div className="mb-4">
                    <strong>Seller Address:</strong> {nft.seller_address}
                  </div>
                  <a
                    href={`https://testnet.xrpl.org/transactions/${nft.transaction_hash}`}
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
