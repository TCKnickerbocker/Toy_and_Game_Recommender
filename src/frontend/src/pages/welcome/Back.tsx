import { Box, Button, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { SignInPage, type AuthProvider } from "@toolpad/core/SignInPage";

export default function WelcomeBackPage() {
  const navigate = useNavigate();
  return (
    <Box>
      <Typography>Welcome Back! What would you like to do?</Typography>
      <Button
        href="/recommendations"
        onClick={() => navigate("recommendations")}
      >
        View My Recommendations
      </Button>
    </Box>
  );
}
