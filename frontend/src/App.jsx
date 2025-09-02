import { useEffect, useState, useRef } from "react";
import axios from "axios";
import './App.css';

function App() {
  const [movies, setMovies] = useState([]);
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [subtitleTracks, setSubtitleTracks] = useState([]);
  const [audioTracks, setAudioTracks] = useState([]);
  const [currentSubtitle, setCurrentSubtitle] = useState(0);
  const [currentAudio, setCurrentAudio] = useState("");
  const [search, setSearch] = useState("");
  const [fullPlayer, setFullPlayer] = useState(true); // default full player
  const [suggestion, setSuggestion] = useState("");
  const videoRef = useRef(null);

  const BACKEND_URL = "/api"; // Nginx proxy to backend

  // Fetch movies from backend
  useEffect(() => {
    axios.get(`${BACKEND_URL}/movies`)
      .then(res => setMovies(res.data.movies))
      .catch(console.error);
  }, []);

  // Fetch tracks for selected movie
  useEffect(() => {
    if (!selectedMovie) return;
    axios.get(`${BACKEND_URL}/tracks/${selectedMovie.name}`)
      .then(res => {
        setSubtitleTracks(res.data.subtitles || []);
        setAudioTracks(res.data.audio || []);
      });
    setCurrentSubtitle(0);
    setCurrentAudio("");
  }, [selectedMovie]);

  const handleSubtitleChange = (idx) => {
    if (!videoRef.current) return;
    for (let i = 0; i < videoRef.current.textTracks.length; i++)
      videoRef.current.textTracks[i].mode = i === idx ? "showing" : "disabled";
    setCurrentSubtitle(idx);
  };

  const handleAudioChange = (idx) => {
    if (!selectedMovie || !videoRef.current) return;
    const url = idx === "" 
      ? `${BACKEND_URL}/stream/${selectedMovie.name}`
      : `${BACKEND_URL}/audio/${selectedMovie.name}/${idx}`;
    const currentTime = videoRef.current.currentTime;
    videoRef.current.src = url;
    videoRef.current.currentTime = currentTime;
    videoRef.current.play();
    setCurrentAudio(idx);
  };

  const handleSuggestionSubmit = () => {
    if (!suggestion.trim()) return;
    axios.post(`${BACKEND_URL}/suggest_movie`, { movie_title: suggestion })
      .then(() => {
        alert("Thanks for your suggestion!");
        setSuggestion("");
      })
      .catch(err => {
        console.error(err);
        alert("Failed to send suggestion.");
      });
  };

  const filteredMovies = movies.filter(m =>
    m.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="App">
      <h1>Puiflix</h1>

      <input
        type="text"
        placeholder="Search..."
        value={search}
        onChange={e => setSearch(e.target.value)}
      />

      <div className="suggestion-box">
        <input
          type="text"
          placeholder="Suggest a movie..."
          value={suggestion}
          onChange={e => setSuggestion(e.target.value)}
        />
        <button onClick={handleSuggestionSubmit}>Send</button>
      </div>

      <div className="movie-grid">
        {filteredMovies.map((movie) => (
          <div
            key={movie.name}
            className="movie-card"
            onClick={() => setSelectedMovie(movie)}
          >
            <img 
              src={`${BACKEND_URL}/posters/${movie.name.replace(/\s+/g,'_')}.jpg`} 
              alt={movie.title} 
            />
            <div className="overlay">
              <span>⭐ {movie.rating || "N/A"}</span>
            </div>
            <p>{movie.title}</p>
          </div>
        ))}
      </div>

      {selectedMovie && (
        <div className={`player-container ${fullPlayer ? "full" : "mini"}`}>
          <video
            ref={videoRef}
            src={`${BACKEND_URL}/stream/${selectedMovie.name}`}
            controls
            width={fullPlayer ? "800" : "400"}
          >
            {subtitleTracks.map((sub, idx) => (
              <track
                key={sub.index}
                label={sub.lang}
                kind="subtitles"
                src={`${BACKEND_URL}/subtitles/${selectedMovie.name}/${sub.index}`}
                default={idx === 0}
              />
            ))}
          </video>

          <div className="controls">
            <select value={currentSubtitle} onChange={e => handleSubtitleChange(parseInt(e.target.value))}>
              {subtitleTracks.map((sub, idx) => (
                <option key={sub.index} value={idx}>{sub.lang}</option>
              ))}
            </select>
            <select value={currentAudio} onChange={e => handleAudioChange(e.target.value)}>
              <option value="">Default</option>
              {audioTracks.map(a => (
                <option key={a.index} value={a.index}>{a.lang}</option>
              ))}
            </select>
            <button onClick={() => setFullPlayer(!fullPlayer)}>
              {fullPlayer ? "Mini Player" : "Full Player"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
