import { Box, Button, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { SignInPage, type AuthProvider } from "@toolpad/core/SignInPage";

const providers = [
  { id: "credentials", name: "Email and Password" },
  // { id: "github", name: "GitHub" },
  // { id: "google", name: "Google" },
  // { id: "facebook", name: "Facebook" },
  // { id: "twitter", name: "Twitter" },
  // { id: "linkedin", name: "LinkedIn" },
];

const signIn: (provider: AuthProvider) => void = async (provider) => {
  const promise = new Promise<void>((resolve) => {
    setTimeout(() => {
      console.log(`Sign in with ${provider.id}`);
      resolve();
    }, 500);
  });
  return promise;
};

export default function LandingPage() {
  return (
    <Box>
      <Typography>Welcome! Please sign into your account.</Typography>
      <Button
        onClick={() => {
          <SignInPage signIn={signIn} providers={providers} />;
        }}
      >
        Sign In
      </Button>
    </Box>
  );
}
