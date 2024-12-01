import Grid from '@mui/material/Grid2';
import React from 'react';

export default function Layout({ children }: { children: React.ReactNode }) {
  return <Grid>{children}</Grid>;
}
