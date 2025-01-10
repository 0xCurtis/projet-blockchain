import Navbar from "./nav";

export default function Page({ children }) {
  return (
    <div className="bg-white min-w-screen min-h-screen w-full overflow-hidden">
      <Navbar />
      <div>{children}</div>
    </div>
  );
}