from flask import Flask, render_template, request, jsonify
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler, MultiLabelBinarizer
import numpy as np
from flasgger import Swagger, swag_from
import os

app = Flask(__name__)
swagger = Swagger(app)

REQUIRED_COLUMNS = ["Const", "Your Rating", "Date Rated", "Title", "Original Title", "URL", "Title Type", "IMDb Rating", "Runtime (mins)", "Year", "Genres", "Num Votes", "Release Date", "Directors"]

def get_recommended_movies():
    my_ratings = pd.read_csv("./data/processed/my_ratings.csv")

    imdb_ratings = pd.read_csv("./data/processed/imdb_movies.csv")
    imdb_ratings = imdb_ratings[imdb_ratings["Num Votes"] > 700]
    imdb_ratings = imdb_ratings[imdb_ratings["Year"] > 1930]

    common_columns = imdb_ratings.columns.intersection(my_ratings.columns).tolist()
    common_columns.append("Your Rating")

    my_ratings_model = my_ratings[common_columns]
    my_ratings_model = my_ratings_model.drop(columns=["Original Title"])

    imdb_ratings_model = imdb_ratings[common_columns[:-1]]
    imdb_ratings_model = imdb_ratings_model.drop(columns=["Original Title"])

    my_ratings_model = my_ratings_model.dropna()
    imdb_ratings_model = imdb_ratings_model.dropna()

    scaler = StandardScaler()
    scaled_my_ratings = scaler.fit_transform(
        my_ratings_model.drop(columns=["Your Rating"])
    )
    scaled_imdb_ratings = scaler.transform(imdb_ratings_model)

    imdb_rating_index = list(imdb_ratings_model.columns).index("IMDb Rating")
    year_index = list(imdb_ratings_model.columns).index("Year")

    scaled_my_ratings[:, imdb_rating_index] *= 3.5
    scaled_imdb_ratings[:, imdb_rating_index] *= 3.5

    year_mean = np.mean(imdb_ratings_model["Year"])
    scaled_imdb_ratings[:, year_index] *= 0.0005
    scaled_imdb_ratings[:, year_index] += year_mean * 0.0005

    combined_ratings = np.hstack(
        (scaled_my_ratings, my_ratings_model[["Your Rating"]].values)
    )
    combined_imdb_ratings = np.hstack(
        (scaled_imdb_ratings, np.zeros((scaled_imdb_ratings.shape[0], 1)))
    )

    model = NearestNeighbors(n_neighbors=20, algorithm="auto", metric="euclidean").fit(
        combined_imdb_ratings
    )
    distances, indices = model.kneighbors(combined_ratings)

    recommended_movies = imdb_ratings.iloc[indices.flatten()]
    recommended_movies_with_title = recommended_movies.join(
        imdb_ratings[["Original Title", "Year"]], rsuffix="_imdb"
    )

    films_watched = my_ratings["Original Title"].tolist()
    recommended_movies_filtered = recommended_movies_with_title[
        ~recommended_movies_with_title["Original Title_imdb"].isin(films_watched)
    ].drop_duplicates(subset=["Original Title_imdb"])

    recommended_movies_filtered = recommended_movies_filtered.rename(
        columns={"Original Title_imdb": "Movie Title"}
    )
    recommended_movies_filtered["Year"] = recommended_movies_filtered["Year"].astype(
        int
    )

    recommended_movies_filtered = recommended_movies_filtered[
        recommended_movies_filtered["IMDb Rating"] > 6.5
    ]

    return recommended_movies_filtered[["Movie Title", "Year", "IMDb Rating"]]


@app.route("/")
@swag_from(
    {
        "responses": {
            200: {
                "description": "A list of recommended movies",
                "examples": {
                    "application/json": [
                        {
                            "Movie Title": "The Shawshank Redemption",
                            "Year": 1994,
                            "IMDb Rating": 9.3,
                        },
                        {
                            "Movie Title": "The Godfather",
                            "Year": 1972,
                            "IMDb Rating": 9.2,
                        },
                    ]
                },
            }
        }
    }
)
def home():
    """
    This is the home endpoint of the movie recommendation API.
    ---
    responses:
      200:
        description: Returns an HTML table of recommended movies.
    """
    recommended_movies = get_recommended_movies()
    table = recommended_movies.to_html(classes="data", header="true", index=False)
    return render_template("index.html", table=table)


@app.route("/upload", methods=["POST"])
@swag_from(
    {
        "parameters": [
            {
                "name": "file",
                "in": "formData",
                "type": "file",
                "required": True,
                "description": "CSV file containing user ratings",
            }
        ],
        "responses": {
            200: {"description": "File uploaded successfully"},
            400: {"description": "Invalid file format or missing required columns"},
        },
        "examples": {
            "curl_command": {
                "summary": "Example CURL command for file upload",
                "value": {
                    "bash": "curl -X POST -F 'file=@/path/to/your/file.csv' http://localhost:5000/upload"
                },
            }
        },
    }
)
def upload_file():
    """
    Upload a CSV file containing user ratings.
    ---
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith(".csv"):
        df = pd.read_csv(file)
        if not all(column in df.columns for column in REQUIRED_COLUMNS):
            return jsonify({"error": "Missing required columns"}), 400

        df = df[df["Title Type"] == "Movie"]
        col_to_drop = ["Const", "Original Title", "URL", "Title Type"]

        for col in col_to_drop:
            df = df.drop(col, axis=1)

        df = df.rename(columns={"Title": "Original Title"})

        datetime_cols = ["Date Rated", "Release Date"]

        for col in datetime_cols:
            df[col] = pd.to_datetime(df[col], format="%Y-%m-%d", errors="coerce")

        df["Released_Year"] = df["Release Date"].dt.year

        df = df.dropna()

        df = df.reset_index(drop=True)

        df["Genres"] = df["Genres"].str.split(", ")
        df["Genres"] = df["Genres"].apply(lambda x: x if isinstance(x, list) else [])

        mlb = MultiLabelBinarizer()
        genres_one_hot = mlb.fit_transform(df["Genres"])

        genres_df = pd.DataFrame(genres_one_hot, columns=mlb.classes_)

        df = pd.concat([df, genres_df], axis=1)

        df = df.drop(["Genres"], axis=1)

        global_mean = df["IMDb Rating"].mean()

        director_counts = df["Directors"].value_counts()

        director_means = df.groupby("Directors")["IMDb Rating"].mean()

        alpha = 10

        smoothed_means = (director_means * director_counts + global_mean * alpha) / (
            director_counts + alpha
        )

        df["directors_encoded"] = df["Directors"].map(smoothed_means)

        df = df.drop(["Directors"], axis=1)

        df.to_csv("./data/processed/my_ratings.csv", index=False)
        return jsonify({"message": "File uploaded successfully"}), 200

    return jsonify({"error": "Invalid file format"}), 400


if __name__ == "__main__":
    if not os.path.exists("./data/processed"):
        os.makedirs("./data/processed")
    app.run(host='0.0.0.0', debug=True)
