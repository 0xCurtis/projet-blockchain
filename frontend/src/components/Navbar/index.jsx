export default function Navbar() {
  return (
    <div className="w-screen bg-gray-800 text-white">
      <div className="container mx-auto flex justify-between items-center py-4">
        <div className="flex items-center">
          <h1 className="text-xl font-bold ml-2">XUMM</h1>
        </div>
        <div className="flex items-center">
          <a href="/" className="mr-4">Mint</a>
          <a href="/list">List</a>
        </div>
      </div>
    </div>
  )
}