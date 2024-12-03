import { StrictMode } from "react";
import { RouterProvider, createBrowserRouter } from "react-router-dom";
import "./css/index.css";
import App from "./App";
import Layout from "./layout";
import { RecommendationsPage, LandingPage } from "./pages";
import { createRoot } from "react-dom/client";

const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    errorElement: <div />,
    children: [
      {
        path: "/",
        element: <LandingPage />,
      },
      {
        path: "/recommendations",
        element: <RecommendationsPage />,
      },
    ],
  },
]);

console.log(router);

const root = createRoot(document.getElementById("root")!);

root.render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
);
