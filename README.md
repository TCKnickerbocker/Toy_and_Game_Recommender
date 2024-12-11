# Amazon Toy and Games Recommender

## Thomas Knickerbocker, Owen Ratgen, Yashas Acharya

NOTE: Each container should have its own .env file before deployment. <br>
So, add a .env file to the following:
- src/api
- src/models/generate_new_products
- src/models/model_1
- src/models/model_2
- src/models/model_3
- src/models/model_4 
<br> And, if running etl pipeline on a container:
- src/etl/configs


### How to Run the Project Locally
1. Open a terminal
2. Go to the src/frontend folder
3. Run command ```npm run start```
4. Open another terminal
5. Go to the src/api folder
6. Run command ```python3 index.py```
7. Open another terminal
8. Go to src/models/generate_new_products
9. Run command ```python3 call_generate_model.py```
10. Open another terminal
11. For each model n:
- Go to src/models/model_n
- Run command ```python3 call_model_n.py```

13. Now you're good to go!

### [Project Plan] (https://docs.google.com/document/d/1dajEkWcu0pIWDITtmJ7vQ9KNjShbRnZYYVwgbx_ofoY/edit?tab=t.gzr8m69bdr1d)
### [Raw Data Structure] (https://docs.google.com/spreadsheets/d/1eK1lWKYCCQQE_UpZJ0EMTd06sOM6jStpfcECJd98mFQ/edit?gid=609464681#gid=609464681)

[Project Plan](https://docs.google.com/document/d/1dajEkWcu0pIWDITtmJ7vQ9KNjShbRnZYYVwgbx_ofoY/edit?tab=t.gzr8m69bdr1d)

[Raw Data Structure](https://docs.google.com/spreadsheets/d/1eK1lWKYCCQQE_UpZJ0EMTd06sOM6jStpfcECJd98mFQ/edit?gid=609464681)


### Put ALL Login info in .env, ensure is in gitignore


