import {
  Box,
  Button,
  Typography,
  Backdrop,
  CircularProgress,
} from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import Grid from "@mui/material/Grid2";
import { RateItem } from "../../components";
import { RateItemProps } from "../../components/RateItem";
import { useNavigate } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import { useEffect, useState } from "react";

export interface ItemData {
  user_id: string;
  product_id: string;
  rating: number;
  favorite: boolean;
}

// Make every new user rate these items to avoid "cold start" with our recommender system
const items: RateItemProps[] = [
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
  // {
  //   productName: "Nice Cube",
  //   description:
  //     "Bring chill vibes with you everywhere with a squeeze of the Nice Cube!",
  //   id: "9",
  //   imgUrl: "https://m.media-amazon.com/images/I/51CfZ8zGq9L._AC_SL1200_.jpg",
  // },
  // {
  //   productName: "PicassoTiles",
  //   description:
  //     "DREAM BIG & BUILD BIG - No limitations, scalable to build as big as desired by adding more pieces to create the master piece. PicassoTiles in colossal styles.",
  //   id: "10",
  //   imgUrl: "https://m.media-amazon.com/images/I/91YckbuDzHL._AC_SL1500_.jpg",
  // },

  // {
  //   productName: "Voice Changer",
  //   description:
  //     "Voice Magic: Transform your voice with 4 thrilling voice-changing modes – Alien, Ghost, Monster, and Robot. Plus, a standard 'Mic' mode for regular amplification. Unleash endless fun and creativity!",
  //   id: "11",
  //   imgUrl: "https://m.media-amazon.com/images/I/81OvZlcB-mL._AC_SX679_.jpg",
  // },
  // {
  //   productName: "Exploding Kittens",
  //   description:
  //     "The card game that gave felines a license to kill. The reason cats around the world are being given the side-eye - it’s Exploding Kittens: Original Edition! This kitty-powered card game is all about turning game night into a blast.",
  //   id: "12",
  //   imgUrl: "https://m.media-amazon.com/images/I/71jTBIqVzRL._AC_SX679_.jpg",
  // },
  // {
  //   productName: "Refasy Piggy Bank Cash",
  //   description:
  //     "【High Quality Materials】:ABS plastic;Safe simulation design,no odor and sturdy and not break easily;An interesting piggy bank specially designed for children.(Applicable Batteries: 3 * 1.5V AA Batteries (not included).)",
  //   id: "13",
  //   imgUrl: "https://m.media-amazon.com/images/I/81Cz2x+ldmL._AC_SL1500_.jpg",
  // },
  // {
  //   productName: "Gross Science Kit",
  //   description:
  //     "SUPER GROSS MEANS SUPER FUN - Science kits are way more fun when the experiments include boiling boogers, creating glowing worms, and making a test tube vomit!",
  //   id: "14",
  //   imgUrl: "https://m.media-amazon.com/images/I/81Aofvl9VoL._AC_SL1500_.jpg",
  // },
  // {
  //   productName: "Barbie Camper Playset",
  //   description:
  //     "Hit the road to adventure with the Barbie Dream Camper featuring an epic slide, 7 play areas and everything imaginations need to play out the ultimate camping trip.",
  //   id: "15",
  //   imgUrl: "https://m.media-amazon.com/images/I/61U0MqmGEsL._AC_SL1000_.jpg",
  // },
  // {
  //   productName: "KOKODI LCD Writing",
  //   description:
  //     "EYE PROTECTION LCD WRITING TABLET: Adopts 2022 LCD pressure-sensitive technology and 10-inch LCD colorful screen.",
  //   id: "16",
  //   imgUrl: "https://m.media-amazon.com/images/I/71JXJ0I9e-L._AC_SL1500_.jpg",
  // },
];

// ? FUTURE: Use Stepper component
export default function RecommendationsPage() {
  const { user } = useAuth0();
  const [isLoading, setIsLoading] = useState(false);
  const [ratings, setRatings] = useState<Record<string, number>>(() =>
    items.reduce((prev, item) => ({ ...prev, [item.id]: 1 }), {}),
  );
  const [favorites, setFavorites] = useState<Record<string, boolean>>(() =>
    items.reduce((prev, item) => ({ ...prev, [item.id]: false }), {}),
  );

  // Calls the Flask API which will insert the user into the DB
  const createUser = async (data: any) => {
    console.log("CREATING USER");
    try {
      const response = await fetch("/api/create_user", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      const responseData = await response.json();
      console.log("Response:", responseData);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  // Runs once when page renders
  useEffect(() => {
    const userData = {
      user_id: user?.user_id,
      email: user?.nickname,
    };
    if (userData.user_id && userData.email) createUser(userData);
  }, [user]);

  // Sets the rating value for a RateItem component when it changes
  const handleRatingChange = (id: string, rating: number) => {
    setRatings((prevRatings) => ({ ...prevRatings, [id]: rating }));
  };

  // Sets the favorite value for a RateItem component when it changes
  const handleFavorites = (id: string, clicked: boolean) => {
    setFavorites((prevFavorites) => ({ ...prevFavorites, [id]: clicked }));
  };

  // Sends a POST request to Flask
  const handleSubmit = async () => {
    let allData: ItemData[] = [];
    for (const item of items) {
      let itemData: ItemData = {
        user_id: user!.user_id,
        product_id: item.id,
        rating: ratings[item.id]!,
        favorite: favorites[item.id]!,
      };
      allData.push(itemData);
    }

    for (const data of allData) {
      try {
        setIsLoading(true);
        const response = await fetch("/api/user_ratings", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(data),
        });

        if (!response.ok) {
          throw new Error("Network response was not ok for user_rating POST");
        }

        const responseData = await response.json();
        console.log("Response:", responseData);
      } catch (error) {
        console.error("Error:", error);
      } finally {
        setIsLoading(false);
      }
    }
  };

  return (
    <Box>
      <Backdrop open={isLoading} style={{ zIndex: 9999 }}>
        <CircularProgress />
      </Backdrop>

      <Box display="flex" justifyContent="center">
        <Typography variant="h6">
          Hey there! Welcome to our Toy and Game Recommender. Rate these items
          and we'll give you recommendations when you refresh the page!
        </Typography>
      </Box>
      <Grid container spacing={2} columns={12}>
        {items.map(({ productName, description, id, imgUrl }, index) => {
          return (
            <Grid size={3} display="flex" justifyContent="center">
              <RateItem
                key={id}
                productName={productName}
                description={description}
                id={id}
                imgUrl={imgUrl}
                onRatingChange={handleRatingChange}
                onFavoriteChange={handleFavorites}
              />
            </Grid>
          );
        })}
      </Grid>

      <Box
        sx={{ display: "flex", alignItems: "center", justifyContent: "center" }}
      >
        <Button
          variant="contained"
          color="success"
          sx={{ marginRight: "20px" }}
          onClick={handleSubmit}
        >
          Submit
        </Button>
        <Button variant="outlined" startIcon={<RefreshIcon />}>
          Refresh
        </Button>
      </Box>
    </Box>
  );
}
