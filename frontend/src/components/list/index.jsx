import {useEffect, useState} from "react";
import Api from "~/apiWrapper/index.jsx";

export default function List() {
  const address = localStorage.getItem("walletAddress");
  const [nfts, setNfts] = useState([]);

  useEffect(() => {
    Api.get(`/api/transaction/nfts/${address}`).then((response) => {
      setNfts(response.data);
    });
  }, [address]);

  return (
    <div className="w-full h-screen text-neutral-1 dark:text-neutral-8 dark:bg-neutral-1">

    </div>
  )
}