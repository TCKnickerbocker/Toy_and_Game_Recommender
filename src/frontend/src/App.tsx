// Top level component, everything runs through this
import { Outlet } from "react-router-dom";
import { Auth0Provider } from "@auth0/auth0-react";

// ? FUTURE: Find a useful MUI component to wrap a page in
export default function App() {
  return (
    <div className="body">
      <div className="content">
        <Auth0Provider
          domain="dev-ns7gd87a4q7hqv1n.us.auth0.com"
          clientId="MrkwzCQhUeOFT8hQ2yoaQHUfEf9g374N"
          authorizationParams={{
            redirect_uri: window.location.origin + "/recommendations",
          }}
        >
          <Outlet />
        </Auth0Provider>
      </div>
    </div>
  );
}
