import {
  Box,
  Button,
  Typography,
  Backdrop,
  CircularProgress,
  Select,
  MenuItem,
} from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import Grid from "@mui/material/Grid2";
import { RateItem } from "../../components";
import { RateItemProps } from "../../components/RateItem";
import { useNavigate } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import { useEffect, useState } from "react";

export interface RatingData {
  user_id: string;
  product_id: string;
  rating: number;
  favorite: boolean;
}

export function extractEmojiSentence(summary: string) {
  const EMOJI_PATTERN =
    /([\u{1F300}-\u{1F64F}\u{1F680}-\u{1F6FF}\u{1F900}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]+)/gu;

  const segments = summary.split(EMOJI_PATTERN);
  const result = [];
  let curr_string = "";
  // Handles gendered emojis that are edge cases for our regex
  const genderSymbols = ["♂", "♀", "⚧"];

  for (let i = 0; i < segments.length; i++) {
    const segment = segments[i].trim();
    if (EMOJI_PATTERN.test(segment)) {
      // If current segment is an emoji, append it with the next text segment
      curr_string = curr_string + segment;
    } else if (genderSymbols.includes(segment)) {
      continue;
    } else {
      // Add non-emoji text segments directly
      curr_string = curr_string + segment;
      result.push(curr_string);
      curr_string = "";
    }
  }

  return result;
}

// ? FUTURE: Use Stepper component
export default function RecommendationsPage() {
  const { user } = useAuth0();
  const [isPageLoading, setisPageLoading] = useState(false);
  const [isCardLoading, setIsCardLoading] = useState(true);
  const [items, setItems] = useState<RateItemProps[]>([]);
  const [refreshesLeft, setRefreshesLeft] = useState(3);
  const [model, setModel] = useState("Model 1");
  const [modelEndpoint, setModelEndpoint] = useState("most_similar_products");

  // TODO: STILL RENDERS AS NOTHING ON RELOAD
  const [userId, setUserId] = useState("");

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
        throw new Error("Network response was not ok for createUser()");
      }

      const responseData = await response.json();
      console.log("Response:", responseData);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  // Gets the initial 8 items for a user
  const getItems = async (kind: string, user_id?: string) => {
    console.log("FETCHING DATA");
    try {
      setItems([]);
      let response;

      if (kind == "similar") {
        response = await fetch(`/api/${modelEndpoint}?user_id=${user_id}`, {
          method: "GET",
        });
      } else {
        response = await fetch("/api/initial_products", { method: "GET" });
      }

      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      const responseData = await response.json();
      console.log(responseData);

      for (const i in responseData) {
        console.log(responseData[i]);

        const itemName = responseData[i]["title"]
          ? responseData[i]["title"]
          : responseData[i][0];
        const itemDescription = responseData[i]["summary"]
          ? responseData[i]["summary"]
          : responseData[i][11];
        const itemId = responseData[i]["productid"]
          ? responseData[i]["productid"]
          : responseData[i][3];
        const imgUrl = responseData[i]["image"]
          ? responseData[i]["image"]
          : responseData[i][8];

        setItems((prevItems) => [
          ...prevItems,
          {
            productName: itemName,
            description: extractEmojiSentence(itemDescription),
            id: itemId,
            imgUrl: imgUrl,
          },
        ]);
      }
      console.log("Response:", responseData);
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setIsCardLoading(false);
    }
  };

  // Runs once when page renders
  useEffect(() => {
    console.log(`USER ID: ${userId}`);
    console.log(user);
    if (user && user.user_id && user.nickname) {
      setUserId(user.user_id);
      const userData = {
        user_id: userId,
        email: user?.nickname,
      };
      createUser(userData);
    }
  }, [user]);

  useEffect(() => {
    getItems("initial");
  }, []);

  useEffect(() => {
    setRatings(items.reduce((prev, item) => ({ ...prev, [item.id]: 1 }), {}));
    setFavorites(
      items.reduce((prev, item) => ({ ...prev, [item.id]: false }), {}),
    );
  }, [items]);

  const [ratings, setRatings] = useState<Record<string, number>>({});
  const [favorites, setFavorites] = useState<Record<string, boolean>>({});

  // console.log("RATINGS: ", ratings);
  // console.log("FAVORITES: ", favorites);

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
    let allData: RatingData[] = [];
    for (const item of items) {
      let itemData: RatingData = {
        user_id: userId,
        product_id: item.id,
        rating: ratings[item.id]!,
        favorite: favorites[item.id]!,
      };
      allData.push(itemData);
    }

    for (const data of allData) {
      try {
        setisPageLoading(true);
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
        setisPageLoading(false);
      }
    }
  };

  const handleRefresh = () => {
    setIsCardLoading(true);
    getItems("similar", userId);
    setRefreshesLeft(refreshesLeft - 1);
    setIsCardLoading(false);
  };

  const handleModelChange = async (event: any) => {
    const modelType = event.target.value;
    setModel(event.target.value);
    if (modelType == "Model 1") {
      console.log("most_similar_products");
      setModelEndpoint("most_similar_products");
    } else if (modelType == "Model 2") {
      console.log("recommend_products_sentiment_model");
      setModelEndpoint("recommend_products_sentiment_model");
    } else if (modelType == "Model 3") {
      console.log("recommend_products_llm_model");
      setModelEndpoint("recommend_products_llm_model");
    } else {
      console.log("recommend_products_similarity_oyt_llm_combined_model");
      setModelEndpoint("recommend_products_similarity_oyt_llm_combined_model");
    }
  };

  // ? FUTURE: Get the cards to have the skeleton and populate with data, one by one instead of all at once
  return (
    <Box>
      <Backdrop open={isPageLoading} style={{ zIndex: 9999 }}>
        <CircularProgress />
      </Backdrop>

      <Box display="flex" justifyContent="center">
        <Typography variant="h6">
          Hey there! Welcome to our Toy and Game Recommender. Rate these items
          and we'll give you recommendations when you refresh the page!
        </Typography>
      </Box>
      <Box display="flex" justifyContent="center">
        <Typography variant="h6">Refreshes Left: {refreshesLeft}</Typography>
      </Box>
      <Box display="flex" justifyContent="center" alignItems="center">
        <Box sx={{ marginRight: "5px" }}>
          <Typography>Which Model do you want to use?</Typography>
        </Box>
        <Box>
          <Select onChange={handleModelChange} label="Model" value={model}>
            <MenuItem value={"Model 1"}>Model 1</MenuItem>
            <MenuItem value={"Model 2"}>Model 2</MenuItem>
            <MenuItem value={"Model 3"}>Model 3</MenuItem>
            <MenuItem value={"Model 4"}>Model 4</MenuItem>
          </Select>
        </Box>
      </Box>
      <Box display="flex" justifyContent="center">
        <Button
          variant="contained"
          sx={{ marginTop: "20px", marginBottom: "20px" }}
          href={`/generate_fake_product?user_id=${userId}`}
        >
          Generate Fake Products
        </Button>
      </Box>
      <Grid container columns={12}>
        {isCardLoading
          ? Array.from({ length: 8 }).map((_, index) => (
              <Grid size={3} display="flex" justifyContent="center">
                <RateItem
                  productName=""
                  description={[]}
                  id={`loading-${index}`}
                  imgUrl=""
                  loading={true}
                  onRatingChange={() => {}}
                  onFavoriteChange={() => {}}
                />
              </Grid>
            ))
          : items.map(({ productName, description, id, imgUrl }, index) => {
              return (
                <Grid size={3} display="flex" justifyContent="center">
                  <RateItem
                    key={id}
                    productName={productName}
                    description={description}
                    id={id}
                    imgUrl={imgUrl}
                    loading={isCardLoading}
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
          disabled={refreshesLeft != 0 ? false : true}
        >
          Submit
        </Button>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleRefresh}
          disabled={refreshesLeft != 0 ? false : true}
        >
          Refresh
        </Button>
      </Box>
    </Box>
  );
}
