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
  const [suggestion, setSuggestion] = useState("");
  const [isMiniPlayer, setIsMiniPlayer] = useState(false); // mini/full toggle
  const videoRef = useRef(null);

  // Fetch movies
  useEffect(() => {
    axios.get("/api/movies")
      .then(res => setMovies(res.data.movies))
      .catch(console.error);
  }, []);

  // Fetch tracks for selected movie
  useEffect(() => {
    if (!selectedMovie) return;
    axios.get(`/api/tracks/${selectedMovie.name}`)
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
      ? `/api/stream/${selectedMovie.name}`
      : `/api/audio/${selectedMovie.name}/${idx}`;
    const currentTime = videoRef.current.currentTime;
    videoRef.current.src = url;
    videoRef.current.currentTime = currentTime;
    videoRef.current.play();
    setCurrentAudio(idx);
  };

  const handleSuggestionSubmit = () => {
    if (!suggestion.trim()) return;
    axios.post("/api/suggest_movie", { movie_title: suggestion })
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

      {/* Suggestion box */}
      <div className="suggestion-box">
        <input
          type="text"
          placeholder="Suggest a movie..."
          value={suggestion}
          onChange={e => setSuggestion(e.target.value)}
        />
        <button onClick={handleSuggestionSubmit}>Send</button>
      </div>

      {/* Movie Grid */}
      <div className="movie-grid">
        {filteredMovies.map((movie) => (
          <div
            key={movie.name}
            className="movie-card"
            onClick={() => setSelectedMovie(movie)}
          >
            <img src={movie.poster} alt={movie.title} />
            <div className="overlay">
              <span>⭐ {movie.rating || "N/A"}</span>
            </div>
            <p>{movie.title}</p>
          </div>
        ))}
      </div>

      {/* Player section */}
      {selectedMovie && (
        <div className={isMiniPlayer ? "mini-player" : "full-player"}>
          <video
            ref={videoRef}
            src={`/api/stream/${selectedMovie.name}`}
            controls
            width={isMiniPlayer ? 400 : "100%"}
            height={isMiniPlayer ? 225 : "auto"}
          >
            {subtitleTracks.map((sub, idx) => (
              <track
                key={sub.index}
                label={sub.lang}
                kind="subtitles"
                src={`/api/subtitles/${selectedMovie.name}/${sub.index}`}
                default={idx === 0}
              />
            ))}
          </video>

          <div className="controls">
            <select
              value={currentSubtitle}
              onChange={e => handleSubtitleChange(parseInt(e.target.value))}
            >
              {subtitleTracks.map((sub, idx) => (
                <option key={sub.index} value={idx}>{sub.lang}</option>
              ))}
            </select>

            <select
              value={currentAudio}
              onChange={e => handleAudioChange(e.target.value)}
            >
              <option value="">Default</option>
              {audioTracks.map(a => (
                <option key={a.index} value={a.index}>{a.lang}</option>
              ))}
            </select>

            <button
              onClick={() => setIsMiniPlayer(!isMiniPlayer)}
            >
              {isMiniPlayer ? "Full Player" : "Mini Player"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
