import { useAuth0 } from "@auth0/auth0-react";
import { Button } from "@mui/material";

// ? FUTURE: Figure out how to redirect a new user to the Welcome New User page automatically
const LoginButton = () => {
  const { loginWithRedirect } = useAuth0();

  return <Button onClick={() => loginWithRedirect()}>Log In</Button>;
};

export default LoginButton;
