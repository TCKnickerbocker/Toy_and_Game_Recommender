import React from 'react';
import ReactDOM from 'react-dom/client';
import { RouterProvider, createBrowserRouter } from 'react-router-dom';
import './index.css';
import App from './App';
import Layout from './layout';
import WelcomeBackPage from './pages/welcome/Back';
import NewUserPage from './pages/welcome/NewUser';
import RecommendationsPage from './pages/recommendations/Recommend';

const router = () => {
  createBrowserRouter([
    {
      path: '/',
      element: <App />,
      errorElement: <div />,
      children: [
        {
          path: '/welcome/back',
          element: <WelcomeBackPage />,
        },
        {
          path: '/welcome/new_user',
          element: <NewUserPage />,
        },
        {
          path: '/recommendations',
          element: <RecommendationsPage />,
        },
      ],
    },
  ]);
};

const root = ReactDOM.createRoot(document.getElementById('root')!);

root.render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
);

// const router = createBrowserRouter([
//   {
//       path: "/",
//       element: <App/>,
//       errorElement: <ErrorPage/>,
//       children: [
//           {
//               index: true,
//               element: <Landing/>,
//               loader: authLoader,
//               errorElement: <ErrorPage/>
//           }, {
//               path: "foods",
//               element: <Foods/>,
//               loader: authLoader,
//               errorElement: <ErrorPage/>
//            },
//           // {
//           //     path: "food/:id",
//           //     element: <Food/>,
//           //     loader: authLoader,
//           //     errorElement: <ErrorPage/>
//           // },
//            {
//               path: "food/edit/:id",
//               element: <EditFood/>,
//               loader: authLoader,
//               errorElement: <ErrorPage/>
//           }, {
//               path: "food/create",
//               element: <CreateFood/>,
//               loader: authLoader,
//               errorElement: <ErrorPage/>
//           }, {
//               path: "recipes",
//               element: <Recipes />,
//               loader: authLoader,
//               errorElement: <ErrorPage/>
//           }, {
//               path: "recipe/:id",
//               element: <Recipe/>,
//               loader: authLoader,
//               errorElement: <ErrorPage/>
//           }, {
//               path: "recipe/edit/:id",
//               element: <EditRecipe/>,
//               loader: authLoader,
//               errorElement: <ErrorPage/>
//           }, {
//               path: "recipe/create",
//               element: <CreateRecipe/>,
//               loader: authLoader,
//               errorElement: <ErrorPage/>
//           }, {
//               path: "queue",
//               element: <RecipeQueue/>,
//               loader: authLoader,
//               errorElement: <ErrorPage/>
//           }]
//   }, {
//       path: "login",
//       element: <Login/>,
//       loader: loginAuthLoader,
//       errorElement: <ErrorPage/>
//   }, {
//       path: "login/redirect",
//       element: <></>,
//       loader: loginRedirectLoader
//   }])

//   const root = ReactDOM.createRoot(document.getElementById('root'));
//   root.render(
//   <React.StrictMode>
//       <RouterProvider router={router} />
//   </React.StrictMode>
//   );
