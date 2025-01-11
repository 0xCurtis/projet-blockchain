// src/components/ErrorPage.jsx
export default function ErrorPage() {
  return (
    <div className="w-full h-screen flex items-center justify-center text-center">
      <h1 className="text-4xl font-bold">Oops!</h1>
      <p className="text-lg">The page you're looking for was not found.</p>
      <a href="/" className="mt-4 text-blue-500 hover:underline">Go back to Home</a>
    </div>
  );
}
