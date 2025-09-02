import { useEffect, useState, useRef } from "react";
import axios from "axios";

function App() {
  const [movies, setMovies] = useState([]);
  const [search, setSearch] = useState("");
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [subtitleTracks, setSubtitleTracks] = useState([]);
  const [audioTracks, setAudioTracks] = useState([]);
  const [currentSubtitle, setCurrentSubtitle] = useState(0);
  const [currentAudio, setCurrentAudio] = useState("");
  const videoRef = useRef(null);
  const [durations, setDurations] = useState({});

  const fetchMovies = () => {
    axios.get("http://localhost:8000/movies")
      .then(res => setMovies(res.data.movies))
      .catch(err => console.error(err));
  };

  useEffect(() => {
    fetchMovies();
    const interval = setInterval(fetchMovies, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!selectedMovie) return;
    const movieName = selectedMovie.name;
    axios.get(`http://localhost:8000/tracks/${movieName}`)
      .then(res => {
        setSubtitleTracks(res.data.subtitles || []);
        setAudioTracks(res.data.audio || []);
      });
    const savedTime = localStorage.getItem(`time-${movieName}`);
    if (videoRef.current && savedTime) videoRef.current.currentTime = parseFloat(savedTime);
  }, [selectedMovie]);

  const handleTimeUpdate = () => {
    if (selectedMovie && videoRef.current) {
      localStorage.setItem(`time-${selectedMovie.name}`, videoRef.current.currentTime);
      setDurations(prev => ({ ...prev, [selectedMovie.name]: videoRef.current.duration }));
    }
  };

  const handleEnded = () => {
    if (selectedMovie) localStorage.removeItem(`time-${selectedMovie.name}`);
  };

  const handleSubtitleChange = (index) => {
    if (!videoRef.current) return;
    for (let i = 0; i < videoRef.current.textTracks.length; i++) {
      videoRef.current.textTracks[i].mode = i === index ? "showing" : "disabled";
    }
    setCurrentSubtitle(index);
  };

  const handleAudioChange = (index) => {
    if (!selectedMovie) return;
    const movieName = selectedMovie.name;
    const url = index === "" 
      ? `http://localhost:8000/stream/${movieName}`
      : `http://localhost:8000/audio/${movieName}/${index}`;
    const currentTime = videoRef.current.currentTime;
    videoRef.current.src = url;
    videoRef.current.currentTime = currentTime;
    videoRef.current.play();
    setCurrentAudio(index);
  };

  const filteredMovies = movies.filter(movie =>
    (movie.title || movie.name).toLowerCase().includes(search.toLowerCase())
  );

  const continueWatching = movies.filter(movie =>
    localStorage.getItem(`time-${movie.name}`)
  );

  const getProgress = (movie) => {
    const savedTime = parseFloat(localStorage.getItem(`time-${movie.name}`)) || 0;
    const duration = durations[movie.name] || 1;
    return Math.min((savedTime / duration) * 100, 100);
  };

  if (selectedMovie) {
    return (
      <div className="bg-black min-h-screen flex flex-col justify-center items-center text-white p-6">
        <div className="w-full max-w-5xl">
          <button
            className="mb-4 px-3 py-1 bg-gray-800 rounded hover:bg-gray-700"
            onClick={() => setSelectedMovie(null)}
          >
            ← Back to Library
          </button>
          <h1 className="text-3xl font-bold mb-4">{selectedMovie.title}</h1>

          <div className="flex gap-4 mb-4">
            {subtitleTracks.length > 0 && (
              <select
                className="p-2 rounded bg-gray-800 text-white"
                value={currentSubtitle}
                onChange={e => handleSubtitleChange(parseInt(e.target.value))}
              >
                {subtitleTracks.map((track, idx) => (
                  <option key={idx} value={idx}>{track.lang || `Sub ${track.index}`}</option>
                ))}
              </select>
            )}

            {audioTracks.length > 0 && (
              <select
                className="p-2 rounded bg-gray-800 text-white"
                value={currentAudio}
                onChange={e => handleAudioChange(e.target.value)}
              >
                <option value="">Default Audio</option>
                {audioTracks.map((track, idx) => (
                  <option key={idx} value={track.index}>{track.lang || track.codec || `Audio ${track.index}`}</option>
                ))}
              </select>
            )}
          </div>

          <video
            ref={videoRef}
            controls
            autoPlay
            className="w-full rounded-xl shadow-lg bg-black"
            onTimeUpdate={handleTimeUpdate}
            onEnded={handleEnded}
          >
            <source src={`http://localhost:8000/stream/${selectedMovie.name}`} type="video/mp4" />
            {subtitleTracks.map((track, idx) => (
              <track
                key={idx}
                src={`http://localhost:8000/subtitles/${selectedMovie.name}/${track.index}`}
                kind="subtitles"
                srcLang={track.lang || "und"}
                label={track.lang || `Sub ${track.index}`}
                default={idx === 0}
              />
            ))}
          </video>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 text-white min-h-screen p-6">
      <h1 className="text-4xl font-bold mb-6">🎬 My Movie Library</h1>

      <input
        type="text"
        placeholder="Search movies..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        className="mb-6 p-2 w-full rounded-lg text-black"
      />

      {continueWatching.length > 0 && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-2">⏯ Continue Watching</h2>
          <div className="flex gap-2 overflow-x-auto pb-2">
            {continueWatching.map(movie => (
              <div key={movie.name} className="flex-none w-24 cursor-pointer" onClick={() => setSelectedMovie(movie)}>
                <img
                  src={`http://localhost:8000${movie.poster}`}
                  alt={movie.title}
                  className="rounded-lg w-24 h-36 object-cover mb-1"
                />
                <div className="relative h-1 bg-gray-600 rounded">
                  <div className="h-1 bg-red-500 rounded" style={{ width: `${getProgress(movie)}%` }} />
                </div>
                <p className="truncate text-xs">{movie.title || movie.name}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-10 gap-2">
        {filteredMovies.map(movie => (
          <div key={movie.name} className="cursor-pointer" onClick={() => setSelectedMovie(movie)}>
            <img
              src={`http://localhost:8000${movie.poster}`}
              alt={movie.title}
              className="rounded-lg w-24 h-36 object-cover mb-1 hover:scale-105 transform transition duration-200"
            />
            <p className="truncate text-xs">{movie.title || movie.name}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
