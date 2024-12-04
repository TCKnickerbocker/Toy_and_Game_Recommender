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

export interface RatingData {
  user_id: string;
  product_id: string;
  rating: number;
  favorite: boolean;
}

// ? FUTURE: Use Stepper component
export default function RecommendationsPage() {
  const { user } = useAuth0();
  const [isPageLoading, setisPageLoading] = useState(false);
  const [isCardLoading, setIsCardLoading] = useState(true);
  const [items, setItems] = useState<RateItemProps[]>([]);
  const [refreshesLeft, setRefreshesLeft] = useState(3);

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

  // Gets the initial 8 items for a user
  const getInitialItems = async () => {
    console.log("FETCHING INITIAL DATA");
    try {
      setItems([]);
      const response = await fetch("/api/initial_products", { method: "GET" });

      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      const responseData = await response.json();
      for (const item of responseData) {
        setItems((prevItems) => [
          ...prevItems,
          {
            productName: item[0],
            description: item[6]
              .trim()
              .slice(1, -1)
              .split('",')
              .map((line: string) => line.trim().replace(/^"/, "")),
            id: item[3],
            imgUrl: item[8],
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
    const userData = {
      user_id: user?.user_id,
      email: user?.nickname,
    };
    if (userData.user_id && userData.email) createUser(userData);
  }, [user]);

  useEffect(() => {
    getInitialItems();
  }, []);

  useEffect(() => {
    setRatings(items.reduce((prev, item) => ({ ...prev, [item.id]: 1 }), {}));
    setFavorites(
      items.reduce((prev, item) => ({ ...prev, [item.id]: false }), {}),
    );
  }, [items]);

  const [ratings, setRatings] = useState<Record<string, number>>({});
  const [favorites, setFavorites] = useState<Record<string, boolean>>({});

  console.log("RATINGS: ", ratings);
  console.log("FAVORITES: ", favorites);

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
        user_id: user!.user_id,
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
    getInitialItems();
    setRefreshesLeft(refreshesLeft - 1);
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
      <Grid container spacing={2} columns={12}>
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