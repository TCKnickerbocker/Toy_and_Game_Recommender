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
  IconButton,
} from "@mui/material";
import FavoriteBorderIcon from "@mui/icons-material/FavoriteBorder";
import FavoriteIcon from "@mui/icons-material/Favorite";
import { useState } from "react";

// ? FUTURE: When parsing productName think about stopping at ",", "+", "-", and any lowercase char. First word?
// ? FUTURE: Think about adding a "Show More" in the future for description
export interface RateItemProps {
  productName: string;
  description: string;
  id: string;
  imgUrl: string;
  onRatingChange?: (id: string, rating: number) => void;
  onFavoriteChange?: (id: string, clicked: boolean) => void;
}

// ? FUTURE: Think about changing to Dialog in the future for sleeker look
export default function RateItem({
  productName,
  description,
  id,
  imgUrl,
  onRatingChange,
  onFavoriteChange,
}: RateItemProps) {
  const [userRating, setUserRating] = useState(0);
  const [favorite, setFavorite] = useState(false);

  const handleRatingChange = (newValue: number) => {
    console.log("CHANGING RATING");
    setUserRating(newValue!);
    onRatingChange!(id, newValue);
  };

  const handleFavorites = () => {
    console.log("FAV VAL: ", !favorite);
    setFavorite(!favorite);
    onFavoriteChange!(id, !favorite);
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
            onChange={(event, newValue) =>
              handleRatingChange(newValue ? newValue : 1)
            }
          />
          <IconButton
            onClick={handleFavorites}
            sx={{
              // border: "1px solid",
              borderColor: "gray",
              // backgroundColor: favorite ? "primary.main" : "transparent",
              color: favorite ? "red" : "inherit",
              "&:hover": {
                backgroundColor: "rgba(0, 0, 0, 0.04)",
              },
            }}
          >
            {favorite ? <FavoriteIcon /> : <FavoriteBorderIcon />}
          </IconButton>
        </CardActions>
      </Card>
    </Box>
  );
}
