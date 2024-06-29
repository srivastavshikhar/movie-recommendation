import streamlit as st
import pickle
import pandas as pd
import requests
def fetch_poster_and_details(movie_id):
    api_key = "8265bd1679663a7ea12ac168da84d2e8"

    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
        response = requests.get(url)
        data = response.json()

        credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={api_key}&language=en-US"
        credits_response = requests.get(credits_url)
        credits_data = credits_response.json()

        trailer_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={api_key}&language=en-US"
        trailer_response = requests.get(trailer_url)
        trailer_data = trailer_response.json()
        trailer_key = trailer_data['results'][0]['key'] if 'results' in trailer_data and len(trailer_data['results']) > 0 else None
        trailer_link = f"https://www.youtube.com/watch?v={trailer_key}" if trailer_key else None

        poster_url = f"https://image.tmdb.org/t/p/w500/{data['poster_path']}" if 'poster_path' in data and data['poster_path'] else None

        movie_details = {
            'overview': data.get('overview', 'No overview available.'),
            'release_date': data.get('release_date', 'N/A'),
            'vote_average': data.get('vote_average', 'N/A'),
            'genres': ', '.join([genre['name'] for genre in data.get('genres', [])]),
            'runtime': data.get('runtime', 'N/A'),
            'director': ', '.join([crew['name'] for crew in credits_data.get('crew', []) if crew['job'] == 'Director']),
            'cast': ', '.join([cast['name'] for cast in credits_data.get('cast', [])[:5]]),
            'trailer_link': trailer_link
        }

    except Exception as e:
        movie_details = {
            'overview': 'No overview available.',
            'release_date': 'N/A',
            'vote_average': 'N/A',
            'genres': 'N/A',
            'runtime': 'N/A',
            'director': 'N/A',
            'cast': 'N/A',
            'trailer_link': None
        }
        poster_url = None
        st.error(f"Error fetching data: {e}")

    return poster_url, movie_details

def recommend(movie, movies_df, similarity_matrix):
    try:
        movie_index = movies_df[movies_df['title'] == movie].index[0]
    except IndexError:
        st.error("Movie not found in the dataset.")
        return []

    distances = similarity_matrix[movie_index]
    similar_movies_indices = sorted(range(len(distances)), key=lambda x: distances[x], reverse=True)[1:6]

    recommendations = []
    for idx in similar_movies_indices:
        movie_id = movies_df.iloc[idx]['movie_id']
        title = movies_df.iloc[idx]['title']
        poster_url, movie_details = fetch_poster_and_details(movie_id)
        recommendations.append((title, poster_url, movie_details))

    return recommendations

movies_dict = pickle.load(open('movie.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl', 'rb'))

st.markdown("""
    <style>
        body, .main {
            background-color: #121212;
            color: white;
        }
        .header {
            text-align: center;
            padding: 20px;
            background-color: #1E1E1E;
            color: white;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .footer {
            text-align: center;
            padding: 10px;
            margin-top: 20px;
            color: #888;
        }
        .movie-title {
            font-size: 1.2em;
            font-weight: bold;
            margin-top: 10px;
        }
        .movie-details {
            margin-top: 10px;
            font-size: 0.9em;
            color: #888;
        }
        .movie-poster {
            border-radius: 10px;
            box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);
            margin-bottom: 10px;
        }
        .recommend-btn {
            text-align: center;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            border: none;
            cursor: pointer;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .stSelectbox>div {
            border-radius: 5px;
            border: 1px solid #888;
            padding: 5px;
            box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);
        }
        .search-bar input {
            width: 100%;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #888;
            margin-bottom: 10px;
            box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="header"><h1>Movie Recommendation System</h1></div>', unsafe_allow_html=True)
st.markdown("### Find movies similar to your favorites!")

search_term = st.text_input('Search for a movie:', key='search')

if search_term:
    filtered_movies = movies[movies['title'].str.contains(search_term, case=False, na=False)]
    if not filtered_movies.empty:
        selected_movie_name = st.selectbox('Select a movie:', filtered_movies['title'].values)
    else:
        st.write('No movies found.')
        selected_movie_name = None
else:
    selected_movie_name = st.selectbox('Select a movie:', movies['title'].values)

if st.button('Recommend'):
    if selected_movie_name:
        with st.spinner('Fetching recommendations...'):
            recommendations = recommend(selected_movie_name, movies, similarity)

        if recommendations:
            st.subheader('Recommended Movies')
            movie_ratings = {}
            for title, poster_url, details in recommendations:
                st.markdown(f'<p class="movie-title">{title}</p>', unsafe_allow_html=True)
                if poster_url:
                    st.image(poster_url, use_column_width=True, caption=title)
                st.markdown(f'<p class="movie-details"><strong>Genres:</strong> {details["genres"]}</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="movie-details"><strong>Overview:</strong> {details["overview"]}</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="movie-details"><strong>Release Date:</strong> {details["release_date"]}</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="movie-details"><strong>Average Vote:</strong> {details["vote_average"]}</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="movie-details"><strong>Runtime:</strong> {details["runtime"]} minutes</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="movie-details"><strong>Director:</strong> {details["director"]}</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="movie-details"><strong>Cast:</strong> {details["cast"]}</p>', unsafe_allow_html=True)
                if details['trailer_link']:
                    st.markdown(f'<p class="movie-details"><a href="{details["trailer_link"]}" target="_blank">Watch Trailer</a></p>', unsafe_allow_html=True)

                # Rating slider
                rating = st.slider(f'Rate {title}', 1, 10, 5, key=f'rate_{title}')
                movie_ratings[title] = rating

            # Display all ratings
            st.subheader('Your Ratings')
            for title, rating in movie_ratings.items():
                st.write(f'{title}: {rating}/10')
        else:
            st.write('No recommendations found.')
    else:
        st.write('Please select a movie.')

if st.checkbox('Show Movie Dataset'):
    st.subheader('Movie Dataset')
    st.write(movies)


st.markdown("""
    <div class="footer">
        <p>Data provided by <a href="https://www.themoviedb.org/" target="_blank" style="color: #4CAF50;">TMDb</a></p>
    </div>
""", unsafe_allow_html=True)
