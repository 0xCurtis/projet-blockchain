import Navbar from "../Navbar/index.jsx";

export default function Page({ children }) {
  return (
    <div className="bg-white min-w-screen min-h-screen w-full overflow-hidden">
      <Navbar />
      <div>{children}</div>
    </div>
  );
}