import { ClerkProvider } from '@clerk/nextjs';
import Grid from '@mui/material/Grid2';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <ClerkProvider>
        <body>
          <Grid>{children}</Grid>
        </body>
      </ClerkProvider>
    </html>
  );
}
