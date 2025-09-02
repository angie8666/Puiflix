import { useRef, useEffect, useState } from "react";

export default function MiniPlayer({ movie, subtitles, audioTracks }) {
  const videoRef = useRef(null);
  const [currentSubtitle, setCurrentSubtitle] = useState(0);
  const [currentAudio, setCurrentAudio] = useState("");
  const [volume, setVolume] = useState(1);
  const [playbackRate, setPlaybackRate] = useState(1);

  useEffect(() => {
    if (!videoRef.current) return;
    videoRef.current.volume = volume;
    videoRef.current.playbackRate = playbackRate;
  }, [volume, playbackRate]);

  const handleSubtitleChange = (idx) => {
    if (!videoRef.current) return;
    for (let i = 0; i < videoRef.current.textTracks.length; i++)
      videoRef.current.textTracks[i].mode = i === idx ? "showing" : "disabled";
    setCurrentSubtitle(idx);
  };

  const handleAudioChange = (idx) => {
    if (!videoRef.current) return;
    const url = idx === "" 
      ? `/api/stream/${movie.name}`
      : `/api/audio/${movie.name}/${idx}`;
    const currentTime = videoRef.current.currentTime;
    videoRef.current.src = url;
    videoRef.current.currentTime = currentTime;
    videoRef.current.play();
    setCurrentAudio(idx);
  };

  return (
    <div className="mini-player">
      <video ref={videoRef} src={`/api/stream/${movie.name}`} controls width="400">
        {subtitles.map((sub, idx) => (
          <track
            key={sub.index}
            label={sub.lang}
            kind="subtitles"
            src={`/api/subtitles/${movie.name}/${sub.index}`}
            default={idx === 0}
          />
        ))}
      </video>
      <div className="controls">
        <select value={currentSubtitle} onChange={e => handleSubtitleChange(parseInt(e.target.value))}>
          {subtitles.map((sub, idx) => <option key={sub.index} value={idx}>{sub.lang}</option>)}
        </select>
        <select value={currentAudio} onChange={e => handleAudioChange(e.target.value)}>
          <option value="">Default</option>
          {audioTracks.map(a => <option key={a.index} value={a.index}>{a.lang}</option>)}
        </select>
        <input type="range" min="0" max="1" step="0.01" value={volume} onChange={e => setVolume(e.target.value)} />
        <select value={playbackRate} onChange={e => setPlaybackRate(Number(e.target.value))}>
          <option value={0.5}>0.5x</option>
          <option value={1}>1x</option>
          <option value={1.25}>1.25x</option>
          <option value={1.5}>1.5x</option>
          <option value={2}>2x</option>
        </select>
      </div>
    </div>
  );
}
