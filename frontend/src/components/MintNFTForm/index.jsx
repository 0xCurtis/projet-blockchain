export const MintNFTForm = ({ metadata, setMetadata, handleMintRWANFT, handleMintNFT, qrCodeMint }) => {
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    const reader = new FileReader();

    reader.onloadend = () => {
      const base64Image = reader.result;
      setMetadata({ ...metadata, image: base64Image });
    };

    if (file) {
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="mt-8">
      <h2 className="text-2xl font-semibold text-gray-800 mb-6">Mint NFT</h2>
      <div className="space-y-4">
        <select
          name="asset_type"
          value={metadata.asset_type}
          onChange={(e) => setMetadata({ ...metadata, asset_type: e.target.value })}
          required
          className="bg-gray-200 text-black w-full px-4 py-2 rounded-lg focus:outline-none focus:ring focus:ring-purple-500 hover:border-purple-700 shadow-lg transition-all"
        >
          <option value="">Select Asset Type</option>
          <option value="Real Estate">Real Estate</option>
          <option value="Fine Art">Fine Art</option>
          <option value="Vehicle">Vehicle</option>
        </select>

        <input
          type="text"
          name="title"
          value={metadata.title}
          onChange={(e) => setMetadata({ ...metadata, title: e.target.value })}
          placeholder="Title"
          className="bg-gray-200 text-black w-full px-4 py-2 rounded-lg focus:outline-none focus:ring focus:ring-purple-500 hover:border-purple-700 shadow-lg transition-all"
        />

        <textarea
          name="description"
          value={metadata.description}
          onChange={(e) => setMetadata({ ...metadata, description: e.target.value })}
          placeholder="Description"
          className="bg-gray-200 text-black w-full px-4 py-2 rounded-lg focus:outline-none focus:ring focus:ring-purple-500 hover:border-purple-700 shadow-lg transition-all"
        />

        <input
          type="text"
          name="location"
          value={metadata.location}
          onChange={(e) => setMetadata({ ...metadata, location: e.target.value })}
          placeholder="Location"
          className="bg-gray-200 text-black w-full px-4 py-2 rounded-lg focus:outline-none focus:ring focus:ring-purple-500 hover:border-purple-700 shadow-lg transition-all"
        />

        <input
          type="file"
          name="image"
          onChange={handleFileChange}
          className="bg-gray-200 text-black w-full px-4 py-2 rounded-lg focus:outline-none focus:ring focus:ring-purple-500 hover:border-purple-700 shadow-lg transition-all"
        />

        <button
          onClick={handleMintRWANFT}
          className="w-full py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition duration-200 mt-6"
        >
          Sign transaction
        </button>
        <button
          onClick={handleMintNFT}
          className="w-full py-3 bg-indigo-600-600 text-white font-semibold rounded-lg hover:bg-green-700 transition duration-200 mt-6"
        >
          Mint NFT
        </button>
      </div>

      {qrCodeMint && (
        <div className="mt-6 flex justify-center">
          <img src={qrCodeMint} alt="QR Code" className="w-64 h-64" />
        </div>
      )}
    </div>
  );
};
