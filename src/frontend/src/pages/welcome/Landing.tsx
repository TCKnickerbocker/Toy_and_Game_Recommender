import { Box, Button, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { LoginButton } from "../../components";

export default function LandingPage() {
  const navigate = useNavigate();
  return (
    <Box>
      <Typography>Welcome! Please sign into your account.</Typography>
      <LoginButton />
    </Box>
  );
}
