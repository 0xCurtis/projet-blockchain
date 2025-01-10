import { RouterProvider } from "react-router-dom";
import { createRoot } from "react-dom/client";
import router from "./routes.jsx";

/* Styles */
import './index.css';
import {AddressProvider} from "~/contexts/address/index.jsx";

createRoot(document.getElementById('root')).render(
  <div className="w-full h-screen text-neutral-1 dark:text-neutral-8 dark:bg-neutral-1">
    <AddressProvider>
      <RouterProvider router={router} />
    </AddressProvider>
  </div>
);
