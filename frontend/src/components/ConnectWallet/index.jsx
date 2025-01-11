// eslint-disable-next-line react/prop-types
export const ConnectWallet = ({ isConnected, connectWithXUMM, qrCode, uuid }) => (
  <>
    {!isConnected ? (
      <div>
        <button
          onClick={connectWithXUMM}
          className="w-full py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition duration-200 mb-6"
        >
          Connect to Wallet
        </button>

        {qrCode && (
          <div className="mt-6 flex justify-center">
            <img src={qrCode} alt="QR Code" className="w-64 h-64" />
          </div>
        )}

        {uuid && (
          <div className="mt-4 text-center">
            <a
              href={`https://xumm.app/sign/${uuid}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              Cliquez ici pour ouvrir le portefeuille et signer la transaction
            </a>
          </div>
        )}
      </div>
    ) : (
      <div className="text-center">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">Wallet Connected</h2>
        <p className="text-gray-700">Votre portefeuille est maintenant connecté !</p>
      </div>
    )}
  </>
);
