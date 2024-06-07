# Movie Recommendation API

This project is a Flask-based API that recommends movies based on your ratings and IMDb ratings.

## Prerequisites

-   Docker
-   Docker Compose

## Setting Up

1.  **Clone the repository:**
    
```bash
git clone https://github.com/jorgedom5/IMDb-Movie-Recommender.git
```
    
2.  **Prepare your environment:**
    
    Make sure you have Docker and Docker Compose installed on your system.
    

## Running the API with Docker Compose

1.  **Build and start the Docker container:**
    
```bash
docker-compose up --build
```
    
This will build the Docker image and start the Flask application. The API will be available at `http://localhost:5000`.
    

## API Endpoints

### Home Endpoint

-   **URL:** `/`
-   **Method:** `GET`
-   **Description:** Returns an HTML table of recommended movies based on the ratings provided.

### Upload File Endpoint

-   **URL:** `/upload`
-   **Method:** `POST`
-   **Description:** Upload a CSV file containing user ratings.


### Example CURL Command for File Upload

To upload your CSV file using CURL, use the following command:

```bash
curl -X POST -F "file=@/path/to/your/file.csv" http://localhost:5000/upload
```

## Preparing the CSV Files

### IMDb Ratings CSV

1.  Download IMDb ratings data and save it as `imdb_movies.csv`.
2.  Ensure the CSV file has the necessary columns: `Original Title`, `Year`, `IMDb Rating`, and `Num Votes`.
3.  Place the file in the `data/processed` directory.

### User Ratings CSV

1.  Create your own ratings CSV file containing the columns `Original Title`, `Year`, `IMDb Rating`, and `Your Rating`.
2.  Upload the file using the `/upload` endpoint as described above.

## Directory Structure

```kotlin
.
├── app.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── data
│   └── processed
│       ├── imdb_movies.csv
│       └── my_ratings.csv
└── templates
    └── index.html
```

## Notes

-   Ensure that the `data/processed` directory exists and contains the necessary CSV files before starting the application.
-   The Flask application is set to run in development mode. For production, you may want to update the configuration accordingly.

## Additional Information

For more information on Docker and Docker Compose, refer to the official documentation:

-   [Docker Documentation](https://docs.docker.com/)
-   [Docker Compose Documentation](https://docs.docker.com/compose/)

## Downloading Your Ratings from IMDb

IMDb allows users to download their ratings in CSV format. Here are the steps to do it:

### Step 1: Log in to IMDb

1.  Open your web browser and go to [IMDb](https://www.imdb.com).
2.  Log in with your IMDb account. If you don't have an account, sign up first.

### Step 2: Access Your User Profile

1.  Once logged in, click on your username at the top right of the page.
2.  From the dropdown menu, select "Your Ratings".

### Step 3: Export Your Ratings

1.  On the ratings page, look for the option to export your data. This is usually found at the top right of the ratings list.
2.  Click on "Export this list".
3.  A CSV file named `ratings.csv` will be downloaded to your computer.

### Step 4: Upload Your Ratings

1.  Once you have the CSV file prepared and correctly formatted, you can upload it to the API using the following CURL command:
    
```bash
curl -X POST -F "file=@/path/to/your/file.csv" http://localhost:5000/upload
```
    

This will upload your ratings into the system and allow you to get personalized movie recommendations through the API.

### Step 5: Verify the Upload

If the upload is successful, you will receive a JSON response with a confirmation message. If there is any error, check the error messages and adjust your CSV file as necessary.

Enjoy your movie recommendations!