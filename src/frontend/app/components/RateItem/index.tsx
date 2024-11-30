import * as React from "react";
import {
  Rating,
  Box,
  Button,
  DialogTitle,
  Dialog,
  DialogContent,
  DialogContentText,
  DialogActions,
  Card,
  Typography,
  CardContent,
} from "@mui/material";

interface RateItemProps {
  product: string;
  description: string;
  id: string;
  img: string;
}

// ? Think about changing to Dialog in the future for sleeker look
export function RateItem({ product, description, id, img }: RateItemProps) {
  return (
    <Box>
      <Card>
        <CardContent>
          <Typography>{product}</Typography>
          <Typography>{description}</Typography>

          <Rating defaultValue={2.5} precision={0.5} />
        </CardContent>
      </Card>
    </Box>
  );
}
