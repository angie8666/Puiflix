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
  const [miniPlayerVisible, setMiniPlayerVisible] = useState(false);
  const videoRef = useRef(null);

  // Fetch movies from backend
  useEffect(() => {
    axios.get("http://localhost:8000/movies")
      .then(res => setMovies(res.data.movies))
      .catch(console.error);
  }, []);

  // Fetch tracks for selected movie
  useEffect(() => {
    if (!selectedMovie) return;
    axios.get(`http://localhost:8000/tracks/${selectedMovie.name}`)
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
      ? `http://localhost:8000/stream/${selectedMovie.name}`
      : `http://localhost:8000/audio/${selectedMovie.name}/${idx}`;
    const currentTime = videoRef.current.currentTime;
    videoRef.current.src = url;
    videoRef.current.currentTime = currentTime;
    videoRef.current.play();
    setCurrentAudio(idx);
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

      {/* Mini-Player */}
      {miniPlayerVisible && selectedMovie && (
        <div className="mini-player">
          <video
            ref={videoRef}
            src={`http://localhost:8000/stream/${selectedMovie.name}`}
            controls
            width="400"
          >
            {subtitleTracks.map((sub, idx) => (
              <track
                key={sub.index}
                label={sub.lang}
                kind="subtitles"
                src={`http://localhost:8000/subtitles/${selectedMovie.name}/${sub.index}`}
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
          </div>
        </div>
      )}

      {/* Full-Screen Movie Page */}
      {selectedMovie && (
        <div className="fullscreen-player">
          <button className="close-btn" onClick={() => setSelectedMovie(null)}>×</button>
          <video
            ref={videoRef}
            src={`http://localhost:8000/stream/${selectedMovie.name}`}
            controls
            autoPlay
          >
            {subtitleTracks.map((sub, idx) => (
              <track
                key={sub.index}
                label={sub.lang}
                kind="subtitles"
                src={`http://localhost:8000/subtitles/${selectedMovie.name}/${sub.index}`}
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
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
