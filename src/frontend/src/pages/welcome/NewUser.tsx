import { Box, Button, Typography } from "@mui/material";
import { RateItem } from "../../components";
import { RateItemProps } from "../../components/RateItem";
import { useNavigate } from "react-router-dom";

// Make every new user rate these items to avoid "cold start" with our recommender system
const coldStartItems: RateItemProps[] = [
  {
    productName: "Lego Christmas Tree",
    description:
      "Grow creativity – Encourage kids to get creative over the holiday season with this LEGO Christmas Tree toy building set",
    id: "1",
    imgUrl:
      "https://images-na.ssl-images-amazon.com/images/I/81sYX-0b5UL._AC_UL900_SR900,600_.jpg",
  },
  {
    productName: "SHASHIBO",
    description:
      "Unlike other puzzle box toys that turn out disappointing & dull, the patented, award-winning shashibo sensory box features 36 rare earth magnets for an innovative design.",
    id: "2",
    imgUrl: "https://m.media-amazon.com/images/I/61Lm9gkTNUL._AC_SL1200_.jpg",
  },
  {
    productName: "Hatchimals Alive",
    description:
      "HATCHES WITH YOUR LOVE: Hatchimals Alive Mystery Hatch surprise eggs are here.",
    id: "3",
    imgUrl: "https://m.media-amazon.com/images/I/81YCL-tG7aL._AC_SL1500_.jpg",
  },
  {
    productName: "Taco Cat Goat Cheese",
    description:
      "PLAY IT ANY TIME ANY PLACE- Convenient take anywhere size game.",
    id: "4",
    imgUrl: "https://m.media-amazon.com/images/I/61B7mux9lIL._AC_SL1500_.jpg",
  },
  {
    productName: "Instant Print Camera",
    description:
      "Funny Instant Print Camera : This kids digital camera with an instant printing function can have a black and white paper photo only 1 second after pressing the shutter.",
    id: "5",
    imgUrl: "https://m.media-amazon.com/images/I/71kp7bAz3BL._AC_SL1500_.jpg",
  },
  {
    productName: "Bitzee",
    description:
      "DIGITAL FRIENDS YOU CAN TOUCH: There are 20 new Bitzee Magicals to collect. They react to your swipes, tilts & touch with sounds & silly interactions.",
    id: "6",
    imgUrl: "https://m.media-amazon.com/images/I/71FOBUEyzCL._AC_SL1500_.jpg",
  },
  {
    productName: "CATAN",
    description:
      "EXPLORE CATAN: Set sail to the uncharted island of Catan and compete with other settlers to establish supremacy.",
    id: "7",
    imgUrl: "https://m.media-amazon.com/images/I/81zZW70yiYL._AC_SL1500_.jpg",
  },
  {
    productName: "Kidnoculars",
    description:
      "SPARK MORE EXPLORATION! Discover the world with science & exploration toys designed just for kids to get up close with nature, peer into outer space, and get smart about science",
    id: "8",
    imgUrl: "https://m.media-amazon.com/images/I/81Aofvl9VoL._AC_SL1500_.jpg",
  },
  {
    productName: "Nice Cube",
    description:
      "Bring chill vibes with you everywhere with a squeeze of the Nice Cube!",
    id: "9",
    imgUrl: "https://m.media-amazon.com/images/I/51CfZ8zGq9L._AC_SL1200_.jpg",
  },
  {
    productName: "PicassoTiles",
    description:
      "DREAM BIG & BUILD BIG - No limitations, scalable to build as big as desired by adding more pieces to create the master piece. PicassoTiles in colossal styles.",
    id: "10",
    imgUrl: "https://m.media-amazon.com/images/I/91YckbuDzHL._AC_SL1500_.jpg",
  },
];

// ? FUTURE: Use Stepper component
export default function NewUserPage() {
  const navigate = useNavigate();
  return (
    <Box>
      <Box>
        <Typography>
          Hey there! Welcome to our Toy and Game Recommender. Since it&apos;s
          your first time here, lets have you rate some items to get a good idea
          of what you&apos;re looking for!
        </Typography>
      </Box>
      <Box sx={{ display: "flex", flexWrap: "wrap" }}>
        {coldStartItems.map(({ productName, description, id, imgUrl }) => {
          return (
            <RateItem
              key={id}
              productName={productName}
              description={description}
              id={id}
              imgUrl={imgUrl}
            />
          );
        })}
      </Box>

      <Box
        sx={{ display: "flex", alignItems: "center", justifyContent: "center" }}
      >
        <Button href="/welcome/back" onClick={() => navigate("/welcome/back")}>
          Next Steps
        </Button>
      </Box>
    </Box>
  );
}
