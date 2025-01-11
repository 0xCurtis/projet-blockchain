import { useEffect, useState } from 'react';
import axios from 'axios';
import {ConnectWallet} from '~/components/ConnectWallet/index.jsx';
import {MintNFTForm} from '~/components/MintNFTForm/index.jsx';
import {QRCodeDisplay} from '~/components/QRCodeDisplay/index.jsx';
import { API_KEY, API_SECRET } from "~/constants/index.jsx";
import Api from "~/apiWrapper/index.jsx";
import { useAddress } from "~/contexts/address/index.jsx";

export default function Home() {
  const [isConnected, setIsConnected] = useState(false);
  const [uuid, setUuid] = useState('');
  const [qrCode, setQrCode] = useState(null);
  const [qrCodeMint, setQrCodeMint] = useState(null);
  const { address, setAddress } = useAddress();
  const [xumResponse, setXumResponse] = useState(null);
  const [template, setTemplate] = useState({
    TransactionType: '',
    Account: '',
    URI: '',
    Flags: 8,
    NFTokenTaxon: 0,
  });
  const [metadata, setMetadata] = useState({
    title: '',
    asset_type: '',
    description: '',
    location: '',
    type: "RWA",
    createdAt: new Date().toISOString(),
    image: '',
  });
  const [txid, setTxid] = useState('');
  const [mintUuid, setMintUuid] = useState('');

  useEffect(() => {
    const storedAddress = localStorage.getItem("walletAddress");
    if (storedAddress) {
      setAddress(storedAddress); // Met à jour le contexte
      setMetadata((prevMetadata) => ({
        ...prevMetadata,
        account: storedAddress,
      }));
      setIsConnected(true);
    }
  }, [setAddress]);

  // region connectWithXUMM
  const pollPayloadStatus = async (uuid) => {
    try {
      const response = await axios.get(`/api/v1/platform/payload/${uuid}`, {
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY,
          'X-API-Secret': API_SECRET,
          'Accept': 'application/json'
        },
      });

      const data = response.data;

      if (data.meta.signed === true) {
        console.log('Payload signé!');
        console.log('Adresse du portefeuille de l\'utilisateur:', data.response.account);

        setAddress(data.response.account); // Met à jour le contexte
        localStorage.setItem("walletAddress", data.response.account); // Sauvegarde dans le localStorage
        setMetadata((prevMetadata) => ({
          ...prevMetadata,
          account: data.response.account,
        }));
        setIsConnected(true);
      } else {
        setTimeout(() => pollPayloadStatus(uuid), 3000);
      }
    } catch (error) {
      console.error('Erreur lors de la vérification du statut du payload:', error);
    }
  };

  const connectWithXUMM = async () => {
    try {
      const response = await axios.post('/api/v1/platform/payload', {
        txjson: { TransactionType: "SignIn" },
        options: {
          pathfinding_fallback: false,
          force_network: "testnet"
        }
      }, {
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY,
          'X-API-Secret': API_SECRET,
          'Accept': 'application/json'
        }
      });

      setUuid(response.data.uuid);
      setQrCode(response.data.refs.qr_png);
      startWebSocket(response.data.refs.websocket_status);
      await pollPayloadStatus(response.data.uuid);
    } catch (error) {
      console.error('Erreur de connexion:', error.response ? error.response.data : error.message);
    }
  };

  const startWebSocket = (websocketUrl) => {
    const socket = new WebSocket(websocketUrl);

    socket.onopen = () => console.log('WebSocket connecté');

    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      console.log('Message du WebSocket:', message);

      if (message.message && message.message.startsWith('Welcome')) {
        console.log('Message d\'accueil reçu');
      } else if (message.expires_in_seconds) {
        console.log('Message d\'expiration reçu', message.expires_in_seconds);
      } else if (message.opened !== undefined) {
        console.log('Connexion ouverte', message.opened);
        setIsConnected(true);
        socket.close();
      }
    };

    socket.onerror = (error) => console.error('Erreur WebSocket:', error);
    socket.onclose = () => console.log('WebSocket fermé');
  };
  // endregion

  //region MINT NFT
  const handleMintRWANFT = async () => {
    Api.post('/api/transaction/nft/mint/template', {
      metadata: metadata,
      account: address,
    })
      .then(response => {
        setTemplate({
          TransactionType: response.template.template.transaction_type,
          Account: address,
          URI: response.template.template.uri,
          Flags: response.template.template.flags,
          NFTokenTaxon: response.template.template.nftoken_taxon,
        });
      })
      .catch(error => {
        console.error('Error minting NFT:', error);
      });
  };

  const handleMintNFT = async () => {
    const payload = {
      txjson: {
        ...template
      },
      options: {
        "pathfinding_fallback": false,
        "force_network": "testnet"
      }
    };

    axios.post('/api/v1/platform/payload', payload, {
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
        'X-API-Secret': API_SECRET,
        'Accept': 'application/json'
      },
    })
      .then(response => {
        setQrCodeMint(response.data.refs.qr_png);
        setMintUuid(response.data.uuid);
      })
      .catch(error => {
        console.error('Erreur lors de la création de la payload:', error);
      });
  };

  useEffect(() => {
    if (!mintUuid) return;

    const fetchPayload = async () => {
      try {
        const timeoutId2 = setTimeout(async () => {
          try {
            const secondResponse = await axios.get(`/api/v1/platform/payload/${mintUuid}`, {
              headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY,
                'X-API-Secret': API_SECRET,
                'Accept': 'application/json'
              },
            });
            console.log('Deuxième réponse:', secondResponse.data);

            setTxid(secondResponse.data.response.txid);
            setXumResponse(secondResponse.data);

          } catch (error) {
            console.error('Erreur lors de la deuxième vérification du statut du payload:', error);
          }
        }, 20000);

        return () => {
          clearTimeout(timeoutId2);
        };
      } catch (error) {
        console.error('Erreur lors de la vérification du statut du payload:', error);
      }
    };

    fetchPayload();
  }, [mintUuid]);

  useEffect(() => {
    if (!txid) return;

    const submitTransaction = async () => {
      try {
        const response = await Api.post('/api/transaction/submit', {
          ...xumResponse,
          metadata: metadata,
          uri: template.URI,
        });
        console.log('Transaction soumise:', response);
      } catch (error) {
        console.error('Erreur lors de la soumission de la transaction:', error);
      }
    };

    submitTransaction();
  }, [txid, xumResponse]);

  return (
    <div className="w-screen bg-gray-100 min-h-screen flex flex-col items-center p-6">
      <div className="bg-white p-8 rounded-lg shadow-xl w-fit">
        <h1 className="text-3xl font-semibold text-center text-gray-800 mb-6">
          Wallet Connection
        </h1>

        {!isConnected ? (
          <ConnectWallet
            isConnected={isConnected}
            connectWithXUMM={connectWithXUMM}
            qrCode={qrCode}
            uuid={uuid}
          />
        ) : (
          <>
            <MintNFTForm
              metadata={metadata}
              setMetadata={setMetadata}
              handleMintRWANFT={handleMintRWANFT}
              handleMintNFT={handleMintNFT}
              qrCodeMint={qrCodeMint}
            />
            <QRCodeDisplay qrCode={qrCodeMint} />
          </>
        )}
      </div>
    </div>
  );
}
