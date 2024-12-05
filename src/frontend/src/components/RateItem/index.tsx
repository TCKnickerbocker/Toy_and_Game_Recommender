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
  Skeleton,
} from "@mui/material";
import FavoriteBorderIcon from "@mui/icons-material/FavoriteBorder";
import FavoriteIcon from "@mui/icons-material/Favorite";
import { useState } from "react";
import { styled } from "@mui/material/styles";
import Collapse from "@mui/material/Collapse";
import Avatar from "@mui/material/Avatar";
import { IconButtonProps } from "@mui/material/IconButton";
import { red } from "@mui/material/colors";
import ShareIcon from "@mui/icons-material/Share";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import MoreVertIcon from "@mui/icons-material/MoreVert";

interface ExpandMoreProps extends IconButtonProps {
  expand: boolean;
}

const ExpandMore = styled((props: ExpandMoreProps) => {
  const { expand, ...other } = props;
  return <IconButton {...other} />;
})(({ theme }) => ({
  marginLeft: "auto",
  transition: theme.transitions.create("transform", {
    duration: theme.transitions.duration.shortest,
  }),
  // variants: [
  //   {
  //     props: ({ expand }) => !expand,
  //     style: {
  //       transform: "rotate(0deg)",
  //     },
  //   },
  //   {
  //     props: ({ expand }) => !!expand,
  //     style: {
  //       transform: "rotate(180deg)",
  //     },
  //   },
  // ],
}));

// ? FUTURE: When parsing productName think about stopping at ",", "+", "-", and any lowercase char. First word?
// ? FUTURE: Think about adding a "Show More" in the future for description
export interface RateItemProps {
  productName: string;
  description: string[];
  id: string;
  imgUrl: string;
  loading?: boolean;
  onRatingChange?: (id: string, rating: number) => void;
  onFavoriteChange?: (id: string, clicked: boolean) => void;
}

// ? FUTURE: Think about changing to Dialog in the future for sleeker look
export default function RateItem({
  productName,
  description,
  id,
  imgUrl,
  loading,
  onRatingChange,
  onFavoriteChange,
}: RateItemProps) {
  const [userRating, setUserRating] = useState(0);
  const [favorite, setFavorite] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const handleExpandClick = () => {
    setExpanded(!expanded);
  };

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
      <Card variant="outlined" sx={{ width: "400px" }}>
        {loading ? (
          <Skeleton
            sx={{ height: "400px", width: "400px", marginBottom: "10px" }}
            animation="wave"
            variant="rectangular"
          />
        ) : (
          <CardMedia
            component="img"
            // height="500"
            image={imgUrl}
            alt="Product Image"
            sx={{
              aspectRatio: "1/1",
              width: "400px",
              height: "400px",
              marginBottom: "10px",
            }}
          />
        )}

        {loading ? (
          <Box
            sx={{
              pt: 0.5,
              marginLeft: "10px",
              height: "150px",
              padding: "16px",
            }}
          >
            <Skeleton width="90%" height="40px" />
            <Skeleton width="90%" height="40px" />
            <Skeleton width="90%" height="40px" />
          </Box>
        ) : (
          <CardHeader
            title={
              productName.length > 110
                ? productName.slice(0, 110) + "..."
                : productName
            }
            sx={{ height: "150px" }}
          />
        )}
        {loading ? (
          <Box display="flex" sx={{ padding: "8px", height: "44px" }}>
            <Skeleton width="30%" height="30px" />
            <Skeleton width="5%" height="30px" sx={{ marginLeft: "10px" }} />
            <Skeleton width="45%" height="30px" sx={{ marginLeft: "55px" }} />
          </Box>
        ) : (
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
            <ExpandMore
              expand={expanded}
              onClick={handleExpandClick}
              aria-expanded={expanded}
              aria-label="show more"
            >
              {!expanded ? "Show Description" : "Hide Description"}
            </ExpandMore>
          </CardActions>
        )}
        <Collapse in={expanded} timeout="auto" unmountOnExit>
          <CardContent>
            {description.map((text) => {
              if (text != "") {
                return <Typography sx={{ marginBottom: 2 }}>{text}</Typography>;
              }
            })}
          </CardContent>
        </Collapse>
      </Card>
    </Box>
  );
}
