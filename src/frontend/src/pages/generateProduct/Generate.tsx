import { Box, Typography } from "@mui/material";
import { useState } from "react";

export default function GenerateProductPage() {
  const [generatedProduct, setGeneratedProduct] = useState("");

  const getGeneratedProduct = async () => {
    console.log("GENERATING PRODUCT");

    try {
      const response = await fetch("/api/generate_fake_product");

      if (!response.ok) {
        throw new Error("Network response for Generating Product was not ok");
      }

      const responseData = await response.json();
      console.log(responseData);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  return (
    <Box>
      <Typography>Generate this</Typography>
    </Box>
  );
}
