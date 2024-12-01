import {
  Rating,
  Box,
  Button,
  Card,
  Typography,
  CardContent,
  CardActions,
  CardMedia,
  CardHeader,
} from "@mui/material";
import { useState } from "react";

// ? FUTURE: When parsing productName think about stopping at ",", "+", "-", and any lowercase char. First word?
// ? FUTURE: Think about adding a "Show More" in the future for description
export interface RateItemProps {
  productName: string;
  description: string;
  id: string;
  imgUrl: string;
}

// ? FUTURE: Think about changing to Dialog in the future for sleeker look
export default function RateItem({
  productName,
  description,
  id,
  imgUrl,
}: RateItemProps) {
  const [userRating, setUserRating] = useState(0);

  // TODO: Send data to Snowflake DB
  const handleSubmit = () => {
    console.log(`${productName}, ${userRating}, ${id}`);
  };

  // ? FUTURE: Make it so one submit button can handle all of these requests
  return (
    <Box
      component="span"
      sx={{ display: "inline-block", mx: "2px", transform: "scale(0.8)" }}
    >
      <Card variant="outlined" sx={{ width: "300px" }}>
        <CardHeader title={productName} />
        <CardMedia
          component="img"
          // height="500"
          image={imgUrl}
          alt="Product Image"
          sx={{ aspectRatio: "1/1", width: "300px", height: "300px" }}
        />
        <CardContent sx={{ height: "150px" }}>
          <Typography>{description}</Typography>
        </CardContent>
        <CardActions disableSpacing>
          <Rating
            defaultValue={0}
            precision={0.5}
            value={userRating}
            onChange={(event, newValue) => setUserRating(newValue!)}
          />
          <Button size="small" onClick={handleSubmit}>
            Submit
          </Button>
        </CardActions>
      </Card>
    </Box>
  );
}
