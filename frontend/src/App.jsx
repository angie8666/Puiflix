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

  // Fetch movies
  useEffect(() => {
    axios.get("http://localhost:8000/movies")
      .then(res => setMovies(res.data.movies))
      .catch(console.error);
  }, []);

  // Fetch audio/subtitles
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

  // Handle subtitle change
  const handleSubtitleChange = (idx) => {
    if (!videoRef.current) return;
    for (let i = 0; i < videoRef.current.textTracks.length; i++)
      videoRef.current.textTracks[i].mode = i === idx ? "showing" : "disabled";
    setCurrentSubtitle(idx);
  };

  // Handle audio change
  const handleAudioChange = (idx) => {
    if (!selectedMovie || !videoRef.current) return;
    const url = idx === "" 
      ? `http://localhost:8000/stream/${selectedMovie.name}`
      : `http://localhost:8000/audio/${selectedMovie.name}/${idx}`;
    const time = videoRef.current.currentTime;
    const paused = videoRef.current.paused;
    videoRef.current.src = url;
    videoRef.current.currentTime = time;
    if (!paused) videoRef.current.play();
    setCurrentAudio(idx);
  };

  // Floating mini-player on scroll
  useEffect(() => {
    const handleScroll = () => {
      if (!selectedMovie) return;
      setMiniPlayerVisible(window.scrollY > 300);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, [selectedMovie]);

  const filteredMovies = movies.filter(m => m.title.toLowerCase().includes(search.toLowerCase()));

  const MovieCard = ({ movie }) => (
    <div className="movie-card" onClick={() => setSelectedMovie(movie)}>
      {movie.poster ? 
        <img src={`http://localhost:8000${movie.poster}`} alt={movie.title} />
        : <div className="poster-skeleton"></div>
      }
      {movie.rating && <div className="rating-badge">{movie.rating}</div>}
      <div className="movie-overlay">
        <strong>{movie.title}</strong><br/>
        {movie.year || ''}<br/>
        {movie.description ? movie.description.substring(0,50) + '...' : ''}
      </div>
    </div>
  );

  return (
    <div style={{ padding: "20px" }}>
      <h1 style={{ fontSize: "28px", fontWeight: "bold", marginBottom: "10px" }}>🎬 Puiflix</h1>
      <input
        type="text"
        placeholder="Search movies..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        style={{ padding: "5px", marginBottom: "20px", width: "300px", borderRadius: "5px" }}
      />

      <div className="scroll-container">
        {filteredMovies.map(movie => <MovieCard key={movie.name} movie={movie} />)}
      </div>

      {/* Movie Modal */}
      {selectedMovie && (
        <div className="modal">
          <div className="modal-content">
            <button className="modal-close" onClick={() => setSelectedMovie(null)}>Close</button>
            <h2>{selectedMovie.title}</h2>

            <div style={{ marginBottom: "10px" }}>
              <select value={currentSubtitle} onChange={e => handleSubtitleChange(parseInt(e.target.value))}
                style={{ padding: "5px", marginRight: "10px" }}>
                {subtitleTracks.length > 0 ? subtitleTracks.map((t,i)=>(
                  <option key={i} value={i}>{t.lang || `Sub ${t.index}`}</option>
                )) : <option value={-1}>No subtitles</option>}
              </select>

              <select value={currentAudio} onChange={e => handleAudioChange(e.target.value)}
                style={{ padding: "5px" }}>
                <option value="">Default Audio</option>
                {audioTracks.length > 0 && audioTracks.map((t,i)=>(
                  <option key={i} value={t.index}>{t.lang || t.codec || `Audio ${t.index}`}</option>
                ))}
              </select>
            </div>

            {/* Single video element for modal & floating mini-player */}
            <video
              ref={videoRef}
              controls
              autoPlay
              style={{
                position: miniPlayerVisible ? "fixed" : "static",
                bottom: miniPlayerVisible ? "20px" : "auto",
                right: miniPlayerVisible ? "20px" : "auto",
                width: miniPlayerVisible ? "300px" : "100%",
                height: miniPlayerVisible ? "170px" : "auto",
                borderRadius: "10px",
                background: "#000",
                zIndex: miniPlayerVisible ? 1001 : "auto"
              }}
            >
              <source src={`http://localhost:8000/stream/${selectedMovie.name}`} type="video/mp4" />
              {subtitleTracks.map((t, i) => (
                <track key={i} src={`http://localhost:8000/subtitles/${selectedMovie.name}/${t.index}`}
                       kind="subtitles" srcLang={t.lang || "und"} label={t.lang || `Sub ${t.index}`} default={i===0}/>
              ))}
            </video>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
