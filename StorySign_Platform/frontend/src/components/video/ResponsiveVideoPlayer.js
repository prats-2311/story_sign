import React, { useState, useRef, useEffect } from "react";
import { useResponsive } from "../../hooks/useResponsive";
import "./ResponsiveVideoPlayer.css";

const ResponsiveVideoPlayer = ({
  src,
  poster,
  autoPlay = false,
  controls = true,
  muted = false,
  loop = false,
  onLoadedData,
  onPlay,
  onPause,
  onEnded,
  onError,
  className = "",
  ...props
}) => {
  const videoRef = useRef(null);
  const containerRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [quality, setQuality] = useState("auto");

  const {
    isMobile,
    isTablet,
    shouldUseVideoOptimizations,
    getVideoQuality,
    windowSize,
  } = useResponsive();

  // Auto-hide controls timer
  const controlsTimeoutRef = useRef(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    // Set optimal quality based on device
    const optimalQuality = getVideoQuality();
    setQuality(optimalQuality);

    // Mobile optimizations
    if (shouldUseVideoOptimizations) {
      video.preload = "metadata"; // Reduce data usage
      video.playsInline = true; // Prevent fullscreen on iOS
    }

    // Event listeners
    const handleLoadedData = () => {
      setIsLoading(false);
      setDuration(video.duration);
      onLoadedData?.(video);
    };

    const handlePlay = () => {
      setIsPlaying(true);
      onPlay?.(video);
    };

    const handlePause = () => {
      setIsPlaying(false);
      onPause?.(video);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      onEnded?.(video);
    };

    const handleError = (e) => {
      setError(e.target.error);
      setIsLoading(false);
      onError?.(e);
    };

    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime);
    };

    const handleVolumeChange = () => {
      setVolume(video.volume);
    };

    video.addEventListener("loadeddata", handleLoadedData);
    video.addEventListener("play", handlePlay);
    video.addEventListener("pause", handlePause);
    video.addEventListener("ended", handleEnded);
    video.addEventListener("error", handleError);
    video.addEventListener("timeupdate", handleTimeUpdate);
    video.addEventListener("volumechange", handleVolumeChange);

    return () => {
      video.removeEventListener("loadeddata", handleLoadedData);
      video.removeEventListener("play", handlePlay);
      video.removeEventListener("pause", handlePause);
      video.removeEventListener("ended", handleEnded);
      video.removeEventListener("error", handleError);
      video.removeEventListener("timeupdate", handleTimeUpdate);
      video.removeEventListener("volumechange", handleVolumeChange);
    };
  }, [
    src,
    onLoadedData,
    onPlay,
    onPause,
    onEnded,
    onError,
    shouldUseVideoOptimizations,
    getVideoQuality,
  ]);

  // Fullscreen handling
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () =>
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
  }, []);

  // Auto-hide controls on mobile
  useEffect(() => {
    if (!isMobile) return;

    const resetControlsTimeout = () => {
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current);
      }

      setShowControls(true);

      if (isPlaying) {
        controlsTimeoutRef.current = setTimeout(() => {
          setShowControls(false);
        }, 3000);
      }
    };

    resetControlsTimeout();

    return () => {
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current);
      }
    };
  }, [isPlaying, isMobile]);

  const togglePlay = () => {
    const video = videoRef.current;
    if (!video) return;

    if (isPlaying) {
      video.pause();
    } else {
      video.play();
    }
  };

  const handleSeek = (newTime) => {
    const video = videoRef.current;
    if (!video) return;

    video.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const handleVolumeChange = (newVolume) => {
    const video = videoRef.current;
    if (!video) return;

    video.volume = newVolume;
    setVolume(newVolume);
  };

  const toggleFullscreen = async () => {
    const container = containerRef.current;
    if (!container) return;

    try {
      if (isFullscreen) {
        await document.exitFullscreen();
      } else {
        await container.requestFullscreen();
      }
    } catch (error) {
      console.error("Fullscreen toggle failed:", error);
    }
  };

  const formatTime = (time) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
  };

  const handleContainerClick = () => {
    if (isMobile) {
      setShowControls(!showControls);
    } else {
      togglePlay();
    }
  };

  const getVideoSources = () => {
    if (typeof src === "string") {
      return [{ src, type: "video/mp4" }];
    }

    // Multiple quality sources
    const sources = [];

    if (src.ultra && !shouldUseVideoOptimizations) {
      sources.push({ src: src.ultra, type: "video/mp4", label: "Ultra" });
    }

    if (src.high && (!shouldUseVideoOptimizations || quality === "high")) {
      sources.push({ src: src.high, type: "video/mp4", label: "High" });
    }

    if (src.medium) {
      sources.push({ src: src.medium, type: "video/mp4", label: "Medium" });
    }

    if (src.low && shouldUseVideoOptimizations) {
      sources.push({ src: src.low, type: "video/mp4", label: "Low" });
    }

    return sources;
  };

  if (error) {
    return (
      <div className={`responsive-video-player error ${className}`}>
        <div className="video-error">
          <div className="error-icon">⚠️</div>
          <div className="error-message">Failed to load video</div>
          <button
            className="retry-button"
            onClick={() => {
              setError(null);
              setIsLoading(true);
              videoRef.current?.load();
            }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={`responsive-video-player ${className} ${
        isFullscreen ? "fullscreen" : ""
      }`}
      onClick={handleContainerClick}
      {...props}
    >
      <video
        ref={videoRef}
        poster={poster}
        autoPlay={autoPlay}
        muted={muted}
        loop={loop}
        playsInline={isMobile}
        controls={false} // We'll use custom controls
        className="video-element"
      >
        {getVideoSources().map((source, index) => (
          <source key={index} src={source.src} type={source.type} />
        ))}
        Your browser does not support the video tag.
      </video>

      {isLoading && (
        <div className="video-loading">
          <div className="loading-spinner"></div>
          <div className="loading-text">Loading video...</div>
        </div>
      )}

      {controls && showControls && !isLoading && (
        <div className="video-controls">
          <div className="controls-top">
            {isMobile && (
              <button
                className="control-button close-button"
                onClick={(e) => {
                  e.stopPropagation();
                  if (isFullscreen) {
                    toggleFullscreen();
                  }
                }}
              >
                ✕
              </button>
            )}
          </div>

          <div className="controls-center">
            <button
              className="control-button play-button"
              onClick={(e) => {
                e.stopPropagation();
                togglePlay();
              }}
            >
              {isPlaying ? "⏸️" : "▶️"}
            </button>
          </div>

          <div className="controls-bottom">
            <div className="progress-container">
              <input
                type="range"
                className="progress-bar"
                min="0"
                max={duration || 0}
                value={currentTime}
                onChange={(e) => handleSeek(parseFloat(e.target.value))}
                onClick={(e) => e.stopPropagation()}
              />
            </div>

            <div className="controls-row">
              <div className="time-display">
                {formatTime(currentTime)} / {formatTime(duration)}
              </div>

              <div className="controls-right">
                {!isMobile && (
                  <div className="volume-control">
                    <button
                      className="control-button volume-button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleVolumeChange(volume > 0 ? 0 : 1);
                      }}
                    >
                      {volume === 0 ? "🔇" : volume < 0.5 ? "🔉" : "🔊"}
                    </button>
                    <input
                      type="range"
                      className="volume-slider"
                      min="0"
                      max="1"
                      step="0.1"
                      value={volume}
                      onChange={(e) =>
                        handleVolumeChange(parseFloat(e.target.value))
                      }
                      onClick={(e) => e.stopPropagation()}
                    />
                  </div>
                )}

                <button
                  className="control-button fullscreen-button"
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleFullscreen();
                  }}
                >
                  {isFullscreen ? "⛶" : "⛶"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResponsiveVideoPlayer;
