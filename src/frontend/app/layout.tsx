import Grid from "@mui/material/Grid2";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Grid>{children}</Grid>
      </body>
    </html>
  );
}
