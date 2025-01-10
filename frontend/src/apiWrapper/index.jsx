/* Modules */
import axios from "axios";
import { toast } from "react-toastify";

/* Constants */
import { BASE_URL } from "~/constants";

export const AxiosInstance = axios.create({
  baseURL: BASE_URL,
});

function handleApiError(e) {
  const errorMessage = e?.response?.data?.data || "An unexpected error occurred. Please try again.";
  toast.error(errorMessage);
  throw e;
}

function wrapRequest(fn) {
  return function wrappedRequest(...args) {
    return fn(...args)
      .then((response) => {
        return response.data;
      })
      .catch(handleApiError);
  };
}

const Api = {
  get get() {
    return wrapRequest(AxiosInstance.get);
  },
  get post() {
    return wrapRequest(AxiosInstance.post);
  },
  get put() {
    return wrapRequest(AxiosInstance.put);
  },
  get patch() {
    return wrapRequest(AxiosInstance.patch);
  },
  get delete() {
    return wrapRequest(AxiosInstance.delete);
  },
  get head() {
    return wrapRequest(AxiosInstance.head);
  },
};

export default Api;