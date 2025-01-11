import {useState, useRef, useEffect} from "react";
import Api from "~/apiWrapper/index.jsx";
import { AiOutlineCheckCircle, AiOutlineCloseCircle } from 'react-icons/ai';
import axios from "axios";
import {API_KEY, API_SECRET} from "~/constants/index.jsx";

export default function List() {
  const address = localStorage.getItem("walletAddress");
  const [nfts, setNfts] = useState([]);
  const [filteredNfts, setFilteredNfts] = useState([]);
  const [selectedType, setSelectedType] = useState("all");
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedNft, setSelectedNft] = useState(null);
  const [priceXrp, setPriceXrp] = useState("");
  const [qrCodes, setQrCodes] = useState({});  // Object to store QR codes by NFT ID
  const modalRef = useRef();

  useEffect(() => {
    if (address) {
      Api.get(`/api/transaction/nfts/${address}`).then((response) => {
        console.log(response);
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

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (modalRef.current && !modalRef.current.contains(e.target)) {
        setModalOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const handleSell = () => {
    if (selectedNft && priceXrp) {
      Api.post("/api/marketplace/list/template", {
        nft_id: selectedNft.nft_id,
        uri: selectedNft.uri,
        price_xrp: priceXrp,
        seller_address: address,
      }).then((res) => {
        axios.post('/api/v1/platform/payload', res.offer_template, {
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY,
            'X-API-Secret': API_SECRET,
            'Accept': 'application/json'
          },
        })
          .then(res => {
            setQrCodes(prevQrCodes => ({
              ...prevQrCodes,
              [selectedNft.nft_id]: res.data.refs.qr_png
            }));
            setTimeout(() => {
              axios.get(`/api/v1/platform/payload/${res.data.uuid}`, {
                headers: {
                  'Content-Type': 'application/json',
                  'X-API-Key': API_KEY,
                  'X-API-Secret': API_SECRET,
                  'Accept': 'application/json'
                }
              }).then(res => {
                const response = res.data;
                Api.post('/api/marketplace/list/submit', {
                  xumm_response: response,
                  nft_id: selectedNft.nft_id,
                }).then((res) => {
                  console.log(res);
                })
              }).catch(error => {
                console.error('Erreur lors de la récupération des données:', error);
              });
            }, 20000);
          })
          .catch(error => {
            console.error('Erreur lors de la création de la payload:', error);
          });
        setModalOpen(false);
      }).catch(() => {
        alert("Erreur lors de la mise en vente du NFT.");
      });
    }
  };


  return (
    <div className="w-full min-h-screen bg-gradient-to-b from-gray-100 to-gray-300 text-neutral-900 dark:text-neutral-100 dark:bg-neutral-800 p-8">
      <div className="container mx-auto">
        <h1 className="text-4xl font-extrabold text-black mb-8 text-center">Liste des NFT</h1>

        {/* Select pour filtrer les NFTs par type */}
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
                    style={{ backgroundColor: !nft.metadata.image ? '#f0f0f0' : 'transparent' }}
                  >
                    <img
                      src={nft.metadata.image || ''}
                      alt={nft.metadata.title}
                      className="w-full h-full object-cover rounded-lg"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.nextSibling.style.display = 'flex';
                      }}
                    />
                    <div className="text-center text-neutral-500 font-bold" style={{ display: 'none' }}>No Image</div>
                  </div>
                  <h2 className="text-2xl font-semibold text-neutral-900 dark:text-white flex items-center relative group">
                    {nft.metadata.title}
                    {nft.metadata_verified ? (
                      <AiOutlineCheckCircle className="ml-2 text-green-500" />
                    ) : (
                      <AiOutlineCloseCircle className="ml-2 text-red-500" />
                    )}
                    <span className="absolute bottom-0 right-0 transform text-sm font-medium text-white bg-neutral-700 px-3 py-1 rounded-md shadow-lg opacity-0 group-hover:opacity-100 transition-all duration-300 ease-in-out">
                      {nft.metadata_verified ? 'Vérifié' : 'Non vérifié'}
                    </span>
                  </h2>
                </div>
                <div className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                  <p className="mb-2"><strong>Description:</strong> {nft.metadata.description}</p>
                  <p className="mb-2"><strong>Localisation:</strong> {nft.metadata.location}</p>
                  <p className="mb-2"><strong>Type:</strong> {nft.metadata.asset_type}</p>
                  <p className="mb-2"><strong>Créé le:</strong> {new Date(nft.created_at).toLocaleString()}</p>
                  <p className="mb-4"><strong>Statut:</strong> {nft.status}</p>
                  <div className="w-full flex justify-between items-center">
                    <a
                      href={`https://testnet.xrpl.org/transactions/${nft.transaction_hash}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 underline transition-colors duration-300"
                    >
                      Voir la transaction
                    </a>
                    <button onClick={() => {setSelectedNft(nft); setModalOpen(true);}} className={`px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition duration-300 ${nft.status === 'listed' ? 'opacity-50 cursor-not-allowed' : ''}`}>
                      {nft.status === 'listed' ? 'Déjà en vente' : 'Mettre en vente'}
                    </button>
                  </div>
                  {selectedNft?.nft_id === nft.nft_id && qrCodes[nft.nft_id] && (
                    <div className="mt-6 flex justify-center">
                      <img src={qrCodes[nft.nft_id]} alt="QR Code" className="w-64 h-64" />
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Modal de vente du NFT */}
      {modalOpen && (
        <div className="fixed inset-0 bg-gray-800 bg-opacity-50 flex justify-center items-center z-50">
          <div
            ref={modalRef}
            className="bg-white dark:bg-neutral-700 p-8 rounded-lg shadow-lg max-w-lg w-full"
          >
            <h2 className="text-3xl font-semibold text-center mb-4 text-neutral-900 dark:text-white">Mettre en vente le NFT</h2>
            <div className="mb-6">
              <label className="block text-lg text-neutral-900 dark:text-white mb-2" htmlFor="price">
                Prix en XRP
              </label>
              <input
                id="price"
                value={priceXrp}
                onChange={(e) => setPriceXrp(e.target.value)}
                className="w-full px-4 py-2 bg-gray-300 rounded-md shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Entrez le prix"
              />
            </div>
            <div className="flex justify-between">
              <button
                onClick={() => setModalOpen(false)}
                className="px-6 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 transition duration-300"
              >
                Annuler
              </button>
              <button
                onClick={handleSell}
                className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition duration-300"
              >
                Confirmer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
