import { useEffect, useRef, useState } from "react";
import VideoAnalyzer from "./VideoAnalyzer";
import {
  ShieldCheck,
  Upload,
  Image as ImageIcon,
  ScanSearch,
  LoaderCircle,
  AlertTriangle,
  CheckCircle2,
  FileImage,
  RotateCcw,
  Video,
  ChevronDown,
  Info,
} from "lucide-react";
import "./App.css";
import "./App.simple-ui.css";

const API_URL = "http://127.0.0.1:8000/analyze";
const MAX_FILE_SIZE = 10 * 1024 * 1024;
const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const HISTOGRAM_CHANNELS = ["red", "green", "blue", "grayscale"];

function formatValue(value, digits = 2) {
  if (value === null || value === undefined || value === "") return "N/A";
  if (typeof value === "number") {
    return Number.isFinite(value) ? value.toFixed(digits) : "N/A";
  }
  return String(value);
}

function getEvidenceLevelClass(level) {
  const normalized = String(level || "").toLowerCase();
  if (normalized.includes("high")) return "evidence-high";
  if (normalized.includes("moderate")) return "evidence-moderate";
  if (normalized.includes("low")) return "evidence-low";
  return "evidence-neutral";
}

function Metric({ label, value }) {
  return (
    <div className="forensics-metric">
      <span>{label}</span>
      <strong>{value ?? "N/A"}</strong>
    </div>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState("image");
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef(null);

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  function selectFile(selectedFile) {
    if (!selectedFile) return;
    if (!ALLOWED_TYPES.includes(selectedFile.type)) {
      setError("Choose a JPG, PNG, or WebP image.");
      return;
    }
    if (selectedFile.size > MAX_FILE_SIZE) {
      setError("Image must be smaller than 10 MB.");
      return;
    }

    setFile(selectedFile);
    setPreview(URL.createObjectURL(selectedFile));
    setResult(null);
    setError("");
  }

  async function analyzeImage() {
    if (!file) {
      setError("Choose an image before starting the analysis.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch(API_URL, { method: "POST", body: formData });
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const detail = typeof data.detail === "string"
          ? data.detail
          : data.detail?.message || "Image analysis failed.";
        throw new Error(detail);
      }
      setResult(data);
    } catch (err) {
      setError(
        err.message === "Failed to fetch"
          ? "Cannot connect to VERITY. Check that FastAPI is running on port 8000."
          : err.message || "An unexpected error occurred."
      );
    } finally {
      setLoading(false);
    }
  }

  function resetAnalysis() {
    setFile(null);
    setPreview("");
    setResult(null);
    setError("");
    if (inputRef.current) inputRef.current.value = "";
  }

  const fakeScore = Number(result?.fake_score ?? 0);
  const realScore = Number(result?.real_score ?? 0);
  const hasValidScores = Number.isFinite(fakeScore) && Number.isFinite(realScore);
  const isPredictedFake = fakeScore > realScore;
  const forensics = result?.forensics;
  const metadata = forensics?.metadata;
  const histogram = forensics?.histogram;
  const colorStats = forensics?.color_statistics;
  const pixelAnalysis = forensics?.pixel_analysis;
  const interpretation = forensics?.interpretation;
  const findings = Array.isArray(interpretation?.findings) ? interpretation.findings : [];

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="VERITY home">
          <span className="brand-icon"><ShieldCheck size={24} /></span>
          <span>VERITY<span className="brand-dot">.</span></span>
        </a>
        <span className="topbar-label"><span className="status-dot" /> AI MEDIA VERIFICATION</span>
      </header>

      <main className="main-content" id="top">
        <section className="hero compact-hero">
          <div className="eyebrow"><ScanSearch size={15} /> SYNTHETIC MEDIA ANALYSIS</div>
          <h1>Check media. <span>Understand the result.</span></h1>
          <p>Run an AI-assisted check on an image or video. Review the assessment first, then open advanced details if you need them.</p>
        </section>

        <nav className="analysis-tabs" aria-label="Choose analysis type">
          <button type="button" className={activeTab === "image" ? "active" : ""} onClick={() => setActiveTab("image")} aria-pressed={activeTab === "image"}>
            <ImageIcon size={18} /> Image analysis
          </button>
          <button type="button" className={activeTab === "video" ? "active" : ""} onClick={() => setActiveTab("video")} aria-pressed={activeTab === "video"}>
            <Video size={18} /> Video analysis
          </button>
        </nav>

        {activeTab === "image" ? (
          <section className="workspace image-workspace">
            <div className="upload-panel">
              <div className="section-heading">
                <div><span className="step-label">IMAGE CHECK</span><h2>Upload an image</h2></div>
                <ImageIcon size={21} />
              </div>

              <label
                className={`dropzone ${preview ? "has-preview" : ""}`}
                onDragOver={(event) => event.preventDefault()}
                onDrop={(event) => { event.preventDefault(); selectFile(event.dataTransfer.files?.[0]); }}
              >
                <input
                  ref={inputRef}
                  id="verity-file-input"
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={(event) => selectFile(event.target.files?.[0])}
                  hidden
                />
                {preview ? (
                  <img className="image-preview" src={preview} alt="Selected image preview" />
                ) : (
                  <div className="upload-prompt">
                    <span className="upload-icon"><Upload size={26} /></span>
                    <strong>Drop an image here</strong>
                    <span>or click to browse</span>
                    <small>JPG, PNG, WebP · Up to 10 MB</small>
                  </div>
                )}
              </label>

              {file && (
                <div className="file-info">
                  <FileImage size={19} />
                  <div className="file-name"><strong>{file.name}</strong><span>{(file.size / 1024 / 1024).toFixed(2)} MB</span></div>
                  <button type="button" className="icon-button" onClick={resetAnalysis} aria-label="Remove selected image"><RotateCcw size={17} /></button>
                </div>
              )}

              <button type="button" className="analyze-button" onClick={analyzeImage} disabled={!file || loading}>
                {loading ? <><LoaderCircle className="spin" size={19} /> Analyzing image…</> : <><ScanSearch size={19} /> Analyze image</>}
              </button>

              {error && <div className="error-message" role="alert"><AlertTriangle size={18} /><span>{error}</span></div>}
              <p className="upload-hint">Your image is sent to the VERITY backend for analysis.</p>
            </div>

            <div className="results-panel">
              <div className="section-heading">
                <div><span className="step-label">REPORT</span><h2>Analysis result</h2></div>
                <ShieldCheck size={22} />
              </div>

              {!result && !loading && (
                <div className="empty-state">
                  <div className="empty-icon"><ScanSearch size={34} /></div>
                  <h3>Your report will appear here</h3>
                  <p>Upload an image and select <strong>Analyze image</strong> to see the model assessment, class scores, and forensic observations.</p>
                  <div className="empty-divider" />
                  <div className="report-feature"><CheckCircle2 size={17} /> AI class scores</div>
                  <div className="report-feature"><CheckCircle2 size={17} /> Visual attention heatmap</div>
                  <div className="report-feature"><CheckCircle2 size={17} /> Optional forensic details</div>
                </div>
              )}

              {loading && <div className="loading-state"><LoaderCircle className="spin" size={34} /><h3>Analyzing image</h3><p>The model and image diagnostics are processing your file.</p></div>}

              {result && (
                <div className="result-content">
                  <div className={`prediction-banner ${isPredictedFake ? "warning" : "success"}`}>
                    {isPredictedFake ? <AlertTriangle size={23} /> : <ShieldCheck size={23} />}
                    <div><span>MODEL ASSESSMENT</span><h3>{result.prediction || "Prediction unavailable"}</h3></div>
                  </div>
                  <p className="result-filename">{result.filename || file?.name || "Uploaded image"}</p>

                  {hasValidScores ? (
                    <>
                      <div className="score-block">
                        <div className="score-header"><span>Fake-class score</span><strong>{fakeScore.toFixed(2)}%</strong></div>
                        <div className="score-track"><div className="score-fill fake-fill" style={{ width: `${Math.min(100, Math.max(0, fakeScore))}%` }} /></div>
                      </div>
                      <div className="score-block">
                        <div className="score-header"><span>Real-class score</span><strong>{realScore.toFixed(2)}%</strong></div>
                        <div className="score-track"><div className="score-fill real-fill" style={{ width: `${Math.min(100, Math.max(0, realScore))}%` }} /></div>
                      </div>
                    </>
                  ) : <p className="forensics-note">The backend did not return valid numeric prediction scores.</p>}

                  <div className="explanation-box">
                    <strong><Info size={17} /> What this result means</strong>
                    <p>{isPredictedFake ? "The model assigned a higher score to the fake class than the real class." : "The model assigned a higher score to the real class than the fake class."}</p>
                    <p>Scores reflect the model output. They do not prove authenticity or identify the exact cause of manipulation.</p>
                  </div>

                  {result.heatmap ? (
                    <div className="heatmap-section">
                      <h3>Visual attention heatmap</h3>
                      <p>Highlighted regions represent relative model attention, not a probability that a region is fake.</p>
                      <img className="heatmap-image" src={`data:image/png;base64,${result.heatmap}`} alt="Model attention heatmap overlay" />
                      <small>Use this as a visual aid, not as proof of manipulation.</small>
                    </div>
                  ) : <div className="heatmap-unavailable"><AlertTriangle size={17} /> Heatmap unavailable for this image.</div>}

                  <details className="advanced-details">
                    <summary><span><ScanSearch size={17} /> Advanced forensic details</span><ChevronDown size={17} /></summary>
                    {!forensics ? (
                      <p className="forensics-note">Forensic analysis is unavailable. Check the backend response and terminal.</p>
                    ) : (
                      <div className="advanced-content">
                        <section className="forensics-section">
                          <div className="forensics-heading"><div><h3>Image metadata</h3><p>File properties and embedded metadata</p></div><span className="forensics-tag">Diagnostic</span></div>
                          <div className="forensics-card">
                            <div className="forensics-grid">
                              <Metric label="Format" value={metadata?.format} />
                              <Metric label="Dimensions" value={metadata?.width != null && metadata?.height != null ? `${metadata.width} × ${metadata.height}` : "N/A"} />
                              <Metric label="Color mode" value={metadata?.mode} />
                              <Metric label="EXIF metadata" value={metadata?.exif_found ? "Available" : "Not found"} />
                            </div>
                            {Object.keys(metadata?.exif || {}).length > 0 && (
                              <div className="exif-list"><h5>Available EXIF fields</h5>{Object.entries(metadata.exif).map(([key, value]) => <div className="exif-row" key={key}><span>{key}</span><strong>{String(value)}</strong></div>)}</div>
                            )}
                            <p className="forensics-note">Missing metadata does not mean an image is fake. Metadata can be removed or modified.</p>
                          </div>
                        </section>

                        <section className="forensics-section">
                          <div className="forensics-heading"><div><h3>Pixel intensity histograms</h3><p>Distribution of channel intensity values</p></div></div>
                          <p className="forensics-description">These charts describe pixel distributions. They do not independently classify an image as real or fake.</p>
                          <div className="histogram-legend"><span className="legend-red">Red</span><span className="legend-green">Green</span><span className="legend-blue">Blue</span><span className="legend-gray">Grayscale</span></div>
                          {!histogram?.channels ? <p className="forensics-note">Histogram data is not available.</p> : HISTOGRAM_CHANNELS.map((channel) => {
                            const counts = Array.isArray(histogram.channels[channel]) ? histogram.channels[channel] : [];
                            const maxCount = Math.max(...counts, 1);
                            const labels = Array.isArray(histogram.labels) ? histogram.labels : [];
                            return <div className="histogram-block" key={channel}>
                              <div className="histogram-title"><span>{channel}</span><span>Low → High intensity</span></div>
                              <div className={`histogram-bars histogram-${channel}`} role="img" aria-label={`${channel} pixel intensity histogram`}>
                                {counts.map((count, index) => <div key={index} className="histogram-bar" title={`${labels[index] ?? index}: ${count} pixels`} style={{ height: `${Math.max(2, (count / maxCount) * 100)}%` }} />)}
                              </div>
                            </div>;
                          })}
                        </section>

                        <section className="forensics-section">
                          <h3>Color statistics</h3>
                          <div className="forensics-card"><div className="forensics-grid">
                            <Metric label="Red mean" value={formatValue(colorStats?.red_mean)} />
                            <Metric label="Green mean" value={formatValue(colorStats?.green_mean)} />
                            <Metric label="Blue mean" value={formatValue(colorStats?.blue_mean)} />
                            <Metric label="Brightness mean" value={formatValue(colorStats?.grayscale_mean)} />
                            <Metric label="Brightness variation" value={formatValue(colorStats?.grayscale_std)} />
                          </div></div>
                        </section>

                        <section className="forensics-section">
                          <h3>Pixel-level diagnostics</h3>
                          <div className="forensics-card"><div className="forensics-grid">
                            <Metric label="Noise residual mean" value={formatValue(pixelAnalysis?.noise_residual_mean)} />
                            <Metric label="Noise residual variation" value={formatValue(pixelAnalysis?.noise_residual_std)} />
                            <Metric label="Edge density" value={pixelAnalysis?.edge_density_percent !== undefined ? `${formatValue(pixelAnalysis.edge_density_percent)}%` : "N/A"} />
                            <Metric label="High-frequency energy" value={formatValue(pixelAnalysis?.high_frequency_energy)} />
                            <Metric label="JPEG quantization tables" value={formatValue(pixelAnalysis?.jpeg_quantization_table_count, 0)} />
                          </div><p className="forensics-note">Compression, resizing, lighting, and editing can affect these measurements. They are not proof of manipulation.</p></div>
                        </section>

                        <section className="findings-section">
                          <div className="findings-header"><div><h3>Forensic findings</h3><p>Interpretation of diagnostic indicators</p></div><span className="findings-count">{findings.length} findings</span></div>
                          {!interpretation ? <p className="findings-note">Findings are unavailable in the backend response.</p> : findings.length === 0 ? <p className="findings-note">No findings were returned for this image.</p> : findings.map((finding, index) => (
                            <article className="finding-card" key={`${finding.category || "finding"}-${index}`}>
                              <div className="finding-top"><span className="finding-category">{finding.category || "General"}</span><span className={`finding-level ${getEvidenceLevelClass(finding.evidence_level)}`}>{finding.evidence_level || "Descriptive"}</span></div>
                              <h4>{finding.title || "Forensic observation"}</h4>
                              <div className="finding-detail"><strong>Observation</strong><p>{finding.observation || "No observation provided."}</p></div>
                              <div className="finding-detail"><strong>Interpretation</strong><p>{finding.interpretation || "No interpretation provided."}</p></div>
                            </article>
                          ))}
                          {interpretation?.conclusion && <div className="findings-conclusion"><strong><Info size={16} /> Overall interpretation</strong><p>{interpretation.conclusion}</p></div>}
                        </section>
                      </div>
                    )}
                  </details>

                  <div className="disclaimer"><AlertTriangle size={17} /><span>AI assessment only. Results can be incorrect. Forensic measurements are descriptive indicators, not independent proof of authenticity.</span></div>
                  <button type="button" className="secondary-button" onClick={resetAnalysis}><RotateCcw size={17} /> Analyze another image</button>
                </div>
              )}
            </div>
          </section>
        ) : (
          <section className="video-workspace">
            <div className="video-intro"><div className="section-heading"><div><span className="step-label">VIDEO CHECK</span><h2>Analyze a video</h2></div><Video size={22} /></div><p>VERITY samples frames from the uploaded video and checks them individually. This is a screening estimate, not proof of authenticity.</p></div>
            <VideoAnalyzer />
          </section>
        )}

        <footer>
          <ShieldCheck size={17} />
          <span>VERITY · AI-assisted media verification prototype</span>
          <span className="footer-note">Not a forensic certification tool</span>
        </footer>
      </main>
    </div>
  );
}
