import streamlit as st
import pandas as pd 
import pickle
import requests
from datetime import datetime

st.set_page_config(layout="wide")

# Custom CSS for better UI
st.markdown("""
    <style>
    .movie-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .movie-info {
        font-size: 0.9rem;
        color: #666;
    }
    .rating {
        color: #ff9800;
        font-weight: bold;
    }
    .genre-tag {
        background-color: #e0e0e0;
        padding: 2px 8px;
        border-radius: 12px;
        margin-right: 5px;
        font-size: 0.8rem;
    }
    .search-container {
        position: relative;
        margin-bottom: 1rem;
    }
    .search-results {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border: 1px solid #ddd;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        z-index: 1000;
        max-height: 400px;
        overflow-y: auto;
    }
    .search-result-item {
        padding: 8px 16px;
        cursor: pointer;
        border-bottom: 1px solid #eee;
    }
    .search-result-item:hover {
        background-color: #f5f5f5;
    }
    .movie-icon {
        color: #666;
        margin-right: 8px;
    }
    .search-input {
        width: 100%;
        padding: 8px 16px;
        font-size: 16px;
        border: 2px solid #ddd;
        border-radius: 24px;
        outline: none;
        transition: all 0.3s;
    }
    .search-input:focus {
        border-color: #1f77b4;
        box-shadow: 0 0 0 2px rgba(31, 119, 180, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

st.title('🎬 Advanced Movie Recommender System')

# Load data
movies_dict = pickle.load(open('movies_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl', 'rb'))

# Initialize session state
if 'selected_movie' not in st.session_state:
    st.session_state.selected_movie = None

# Create a container for search
search_container = st.container()

with search_container:
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    
    # Search box
    search_query = st.text_input("", placeholder="🔍 Search for a movie...", key="search")
    
    # Show filtered movies based on search
    if search_query:
        filtered_movies = movies[movies['title'].str.contains(search_query, case=False)].head(8)
        if not filtered_movies.empty:
            st.markdown('<div class="search-results">', unsafe_allow_html=True)
            for idx, movie in filtered_movies.iterrows():
                if st.button(f"🎬 {movie['title']}", 
                           key=f"{movie['title']}_{idx}",
                           help="Click to select this movie"):
                    st.session_state.selected_movie = movie['title']
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Get selected movie
selected_movie_name = st.session_state.selected_movie

def fetch_movie_details(movie_id):
    try:
        response = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}?api_key=a1329097a5e56ecb39c3fa12fbf78677&language=en-US')
        data = response.json()
        
        # Extract genres
        genres = [genre['name'] for genre in data.get('genres', [])]
        
        return {
            'overview': data.get('overview', 'No overview available'),
            'release_date': data.get('release_date', 'Unknown'),
            'rating': data.get('vote_average', 0),
            'runtime': data.get('runtime', 0),
            'popularity': data.get('popularity', 0),
            'genres': genres
        }
    except Exception as e:
        st.error(f"Error fetching movie details: {str(e)}")
        return None

def fetch_poster(movie_id):
    try:
        response = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}?api_key=a1329097a5e56ecb39c3fa12fbf78677&language=en-US')
        data = response.json()
        if 'poster_path' in data and data['poster_path']:
            return 'https://image.tmdb.org/t/p/w500/' + data['poster_path']
        return 'https://via.placeholder.com/500x750.png?text=No+Poster+Available'
    except Exception as e:
        st.error(f"Error fetching poster: {str(e)}")
        return 'https://via.placeholder.com/500x750.png?text=Error+Loading+Poster'

def recommend(selected_movie_name):
    movie_index = movies[movies['title'] == selected_movie_name].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
    
    recommended_movies = []
    recommended_movies_poster = []
    movie_details = []
    
    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_movies_poster.append(fetch_poster(movie_id))
        details = fetch_movie_details(movie_id)
        if details:
            movie_details.append(details)
        else:
            movie_details.append({
                'overview': 'Details not available',
                'release_date': 'Unknown',
                'rating': 0,
                'runtime': 0,
                'popularity': 0,
                'genres': []
            })
    
    return recommended_movies, recommended_movies_poster, movie_details

# Display selected movie details
if selected_movie_name:
    st.markdown("---")
    movie_idx = movies[movies['title'] == selected_movie_name].index[0]
    movie_id = movies.iloc[movie_idx].movie_id
    details = fetch_movie_details(movie_id)
    
    if details:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(fetch_poster(movie_id), width=300)
        with col2:
            st.markdown(f"### {selected_movie_name}")
            
            # Display genres
            if details['genres']:
                genre_html = ' '.join([f'<span class="genre-tag">{genre}</span>' for genre in details['genres']])
                st.markdown(f"<div>{genre_html}</div>", unsafe_allow_html=True)
            
            st.markdown(f"**Release Date:** {details['release_date']}")
            st.markdown(f"**Rating:** {'⭐' * int(details['rating']/2)} ({details['rating']}/10)")
            st.markdown(f"**Runtime:** {details['runtime']} minutes")
            st.markdown(f"**Popularity Score:** {details['popularity']:.1f}")
            st.markdown("**Overview:**")
            st.write(details['overview'])

        if st.button('🎯 Get Recommendations', key=f"get_recommendations_{selected_movie_name}"):
    
            
            st.markdown("---")
            st.markdown("### Recommended Movies")
            names, posters, details = recommend(selected_movie_name)
            
            cols = st.columns(5)
            for idx, (col, name, poster, detail) in enumerate(zip(cols, names, posters, details)):
                with col:
                    st.image(poster)
                    st.markdown(f"<div class='movie-title'>{name}</div>", unsafe_allow_html=True)
                    
                    # Display genres for each recommendation
                    if detail['genres']:
                        genre_html = ' '.join([f'<span class="genre-tag">{genre}</span>' for genre in detail['genres'][:2]])
                        st.markdown(f"<div>{genre_html}</div>", unsafe_allow_html=True)
                    
                    st.markdown(f"<div class='movie-info'>⭐ {detail['rating']}/10</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='movie-info'>🎬 {detail['runtime']} min</div>", unsafe_allow_html=True)
                    if detail['release_date'] != 'Unknown':
                        release_year = detail['release_date'].split('-')[0]
                        st.markdown(f"<div class='movie-info'>📅 {release_year}</div>", unsafe_allow_html=True)
                    with st.expander("Overview"):
                        st.write(detail['overview'])
