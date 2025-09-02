export default function MovieCard({ movie, onSelect }) {
  return (
    <div className="movie-card" onClick={() => onSelect(movie)}>
      <img src={movie.poster} alt={movie.title} />
      <div className="overlay">
        <span>⭐ {movie.rating || "N/A"}</span>
      </div>
      <p>{movie.title}</p>
    </div>
  );
}
