import { useEffect, useState } from "react";
import axios from "axios";

function App() {
  const [movies, setMovies] = useState([]);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    axios.get("http://localhost:8000/movies")
      .then(res => setMovies(res.data.movies))
      .catch(err => console.error(err));
  }, []);

  return (
    <div className="p-6 bg-gray-900 text-white min-h-screen">
      <h1 className="text-3xl font-bold mb-6">🎬 My Local Movie Library</h1>

      <div className="grid grid-cols-3 gap-4">
        {movies.map(movie => (
          <div
            key={movie}
            className="p-4 bg-gray-700 rounded-xl cursor-pointer hover:bg-gray-600"
            onClick={() => setSelected(movie)}
          >
            {movie}
          </div>
        ))}
      </div>

      {selected && (
        <div className="mt-6">
          <h2 className="text-xl mb-2">Now Playing: {selected}</h2>
          <video
            src={`http://localhost:8000/stream/${selected}`}
            controls
            className="w-full rounded-xl shadow-lg"
          />
        </div>
      )}
    </div>
  );
}

export default App;
