import { createBrowserRouter } from "react-router-dom";
import Page from "~/components/Page.jsx";
import Home from "~/pages/Home/index.jsx";
import ErrorPage from "~/components/error/index.jsx";
import List from "~/components/list/index.jsx";
import ProtectedRoute from "~/components/protectedRoute";

const routes = [
  {
    path: "/",
    element: <Home />,
    protected: false,
  },
  {
    path: "/home",
    element: <Home />,
    protected: false,
  },
  {
    path: "/list",
    element: <List />,
    protected: false,
  },
];

const computeRoutes = (routes) => {
  return routes.map((route) => {
    const element = route.protected ? (
      <ProtectedRoute>{route.element}</ProtectedRoute>
    ) : (
      route.element
    );

    return {
      path: route.path,
      element: <Page>{element}</Page>,
      errorElement: <ErrorPage />,
    };
  });
};

const router = createBrowserRouter(computeRoutes(routes));

export default router;
