import { useState, useEffect } from "react";
import axios from "axios";
import MovieCard from "./components/MovieCard";
import MiniPlayer from "./components/MiniPlayer";
import './App.css';

function App() {
  const [movies, setMovies] = useState([]);
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [subtitles, setSubtitles] = useState([]);
  const [audioTracks, setAudioTracks] = useState([]);
  const [search, setSearch] = useState("");
  const [suggestion, setSuggestion] = useState("");

  useEffect(() => {
    axios.get("/api/movies").then(res => setMovies(res.data.movies));
  }, []);

  useEffect(() => {
    if (!selectedMovie) return;
    axios.get(`/api/tracks/${selectedMovie.name}`).then(res => {
      setSubtitles(res.data.subtitles || []);
      setAudioTracks(res.data.audio || []);
    });
  }, [selectedMovie]);

  const filteredMovies = movies.filter(m => m.title.toLowerCase().includes(search.toLowerCase()));

  const handleSuggestionSubmit = () => {
    if (!suggestion.trim()) return;
    axios.post("/api/suggest", { title: suggestion }).then(() => {
      alert("Thanks for your suggestion!");
      setSuggestion("");
    });
  };

  return (
    <div className="App">
      <h1>Puiflix</h1>

      <input type="text" placeholder="Search..." value={search} onChange={e => setSearch(e.target.value)} />

      <div className="suggestion-box">
        <input type="text" placeholder="Suggest a movie..." value={suggestion} onChange={e => setSuggestion(e.target.value)} />
        <button onClick={handleSuggestionSubmit}>Send</button>
      </div>

      <div className="movie-grid">
        {filteredMovies.map(movie => <MovieCard key={movie.name} movie={movie} onSelect={setSelectedMovie} />)}
      </div>

      {selectedMovie && <MiniPlayer movie={selectedMovie} subtitles={subtitles} audioTracks={audioTracks} />}
    </div>
  );
}

export default App;
