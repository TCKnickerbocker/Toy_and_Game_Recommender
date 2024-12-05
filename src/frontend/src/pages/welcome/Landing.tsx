import { Box, Button, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { LoginButton } from "../../components";

export default function LandingPage() {
  const navigate = useNavigate();
  return (
    <Box>
      <Box display="flex" justifyContent="center">
        <Typography>Welcome! Please sign into your account.</Typography>
      </Box>
      <Box display="flex" justifyContent="center">
        <LoginButton />
      </Box>
    </Box>
  );
}
