import { RateItem } from "../../components";
import { useAuth0 } from "@auth0/auth0-react";
import { Backdrop, Box, Button, CircularProgress } from "@mui/material";
import Grid from "@mui/material/Grid2";
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { extractEmojiSentence } from "../recommendations/Recommend";

export default function GenerateProductPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [userId, setUserId] = useState(searchParams.get("user_id"));
  const [generatedProduct, setGeneratedProduct] = useState([]);
  const [isPageLoading, setisPageLoading] = useState(false);
  const imgPlaceholderUrl =
    "https://redthread.uoregon.edu/files/original/affd16fd5264cab9197da4cd1a996f820e601ee4.png";

  const getGeneratedProduct = async () => {
    console.log("GENERATING PRODUCT");
    setisPageLoading(true);

    try {
      const response = await fetch(
        `/api/generate_fake_product?user_id=${userId}&num_products=1`,
      );

      if (!response.ok) {
        throw new Error("Network response for Generating Product was not ok");
      }

      const responseData = await response.json();
      setGeneratedProduct(responseData);
      console.log(responseData);
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setisPageLoading(false);
    }
  };

  const handleGeneration = async () => {
    getGeneratedProduct();
  };

  return (
    <Box>
      <Backdrop open={isPageLoading} style={{ zIndex: 9999 }}>
        <CircularProgress />
      </Backdrop>
      <Box display="flex" justifyContent="center">
        <Button onClick={handleGeneration} variant="contained">
          Generate Products
        </Button>
      </Box>
      <Grid container columns={12}>
        {generatedProduct ? (
          generatedProduct.map((product: any) => {
            return (
              <Grid size={4} display="flex" justifyContent="center">
                <RateItem
                  productName={product.title}
                  description={extractEmojiSentence(product.summary)}
                  id={product.productId}
                  imgUrl={
                    product.imageUrl ? product.imageUrl : imgPlaceholderUrl
                  }
                />
              </Grid>
            );
          })
        ) : (
          <></>
        )}
      </Grid>
    </Box>
  );
}
