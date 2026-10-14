
import { useState } from "react";

import {
  Film,
  Upload,
  LoaderCircle,
  AlertTriangle,
  Video,
} from "lucide-react";

const VIDEO_API_URL = "http://127.0.0.1:8000/analyze-video";
const MAX_VIDEO_SIZE = 100 * 1024 * 1024;

const ALLOWED_VIDEO_TYPES = [
  "video/mp4",
  "video/quicktime",
  "video/x-msvideo",
  "video/x-matroska",
  "video/webm",
];

export default function VideoAnalyzer() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  function selectVideo(selectedFile) {
    if (!selectedFile) return;

    const extension = selectedFile.name
      .split(".")
      .pop()
      .toLowerCase();

    const allowedExtensions = [
      "mp4", "mov", "avi", "mkv", "webm",
    ];

    if (
      !ALLOWED_VIDEO_TYPES.includes(selectedFile.type) &&
      !allowedExtensions.includes(extension)
    ) {
      setError("Please choose a supported video file.");
      return;
    }

    if (selectedFile.size > MAX_VIDEO_SIZE) {
      setError("Video size must not exceed 100 MB.");
      return;
    }

    setFile(selectedFile);
    setResult(null);
    setError("");
  }

  async function analyzeVideo() {
    if (!file) {
      setError("Please select a video first.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(VIDEO_API_URL, {
        method: "POST",
        body: formData,
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data.detail || "Video analysis failed."
        );
      }

      setResult(data);
    } catch (err) {
      setError(
        err.message === "Failed to fetch"
          ? "Cannot reach the FastAPI backend on port 8000."
          : err.message
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="video-tool">
      <div className="video-tool-heading">
        <div>
          <span className="step-label">VIDEO ANALYSIS</span>
          <h2>Video deepfake screening</h2>
          <p>
            Analyze selected frames using the existing image
            classification model.
          </p>
        </div>

        <Video size={25} />
      </div>

      <label className="video-dropzone">
        <input
          type="file"
          accept=".mp4,.mov,.avi,.mkv,.webm,video/*"
          onChange={(event) =>
            selectVideo(event.target.files?.[0])
          }
          hidden
        />

        <span className="upload-icon">
          <Upload size={25} />
        </span>

        <strong>
          {file ? file.name : "Choose a video"}
        </strong>

        <span>
          MP4, MOV, AVI, MKV, or WebM · Maximum 100 MB
        </span>
      </label>

      {file && (
        <p className="video-file-size">
          {(file.size / 1024 / 1024).toFixed(2)} MB
        </p>
      )}

      <button
        type="button"
        className="analyze-button"
        onClick={analyzeVideo}
        disabled={!file || loading}
      >
        {loading ? (
          <>
            <LoaderCircle className="spin" size={19} />
            Analyzing video frames...
          </>
        ) : (
          <>
            <Film size={19} />
            Analyze video
          </>
        )}
      </button>

      {loading && (
        <p className="video-note">
          CPU inference can take some time. Keep this page open.
        </p>
      )}

      {error && (
        <div className="error-message" role="alert">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {result && (
        <div className="video-report">
          <div
            className={`prediction-banner ${
              result.average_fake_score >
              result.average_real_score
                ? "warning"
                : "success"
            }`}
          >
            <Film size={23} />

            <div>
              <span>VIDEO MODEL ASSESSMENT</span>
              <h3>{result.prediction}</h3>
            </div>
          </div>

          <p className="result-filename">
            {result.filename}
          </p>

          <div className="video-stats-grid">
            <div className="video-stat">
              <span>Duration</span>
              <strong>
                {result.duration_seconds} sec
              </strong>
            </div>

            <div className="video-stat">
              <span>Frames analyzed</span>
              <strong>{result.frames_analyzed}</strong>
            </div>

            <div className="video-stat">
              <span>Average fake score</span>
              <strong>
                {result.average_fake_score}%
              </strong>
            </div>

            <div className="video-stat">
              <span>Average real score</span>
              <strong>
                {result.average_real_score}%
              </strong>
            </div>
          </div>

          <h3>Frame-by-frame results</h3>

          <div className="video-frame-list">
            {result.frame_results?.map((frame) => (
              <article
                className="video-frame-card"
                key={frame.frame_number}
              >
                <div>
                  <strong>
                    {Math.floor(frame.timestamp_seconds / 60)}:
                    {String(
                      Math.floor(frame.timestamp_seconds % 60)
                    ).padStart(2, "0")}
                  </strong>

                  <span>
                    Frame {frame.frame_number}
                  </span>
                </div>

                <div>
                  <span>{frame.prediction}</span>
                  <small>
                    Fake {frame.fake_score}% · Real{" "}
                    {frame.real_score}%
                  </small>
                </div>
              </article>
            ))}
          </div>

          <div className="findings-conclusion">
            <strong>
              <AlertTriangle size={17} />
              Important limitation
            </strong>

            <p>{result.warning}</p>
          </div>

          <button
            type="button"
            className="secondary-button"
            onClick={() => {
              setFile(null);
              setResult(null);
              setError("");
            }}
          >
            Analyze another video
          </button>
        </div>
      )}
    </section>
  );
}
