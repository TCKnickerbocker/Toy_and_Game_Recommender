import { Box, Button, Typography } from '@mui/material';

export default function WelcomeBackPage() {
  return (
    <Box>
      <Typography>Welcome Back! What would you like to do?</Typography>
      <Button href="/recommendations">View My Recommendations</Button>
    </Box>
  );
}
