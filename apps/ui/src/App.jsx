import React, { useState, useRef } from 'react';
import { 
  Upload, 
  FileText, 
  CheckCircle, 
  TrendingUp, 
  Users, 
  DollarSign, 
  ShieldAlert, 
  Zap, 
  Cpu, 
  Loader2,
  Activity,
  Layers
} from 'lucide-react';

export default function App() {
  // Form State
  const [startupName, setStartupName] = useState('');
  const [sector, setSector] = useState('Artificial Intelligence');
  const [stage, setStage] = useState('SEED');
  const [amount, setAmount] = useState('');
  
  // File Upload State
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedFilePath, setUploadedFilePath] = useState('');
  
  // Analysis Pipeline Execution State
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  const fileInputRef = useRef(null);

  // Triggered when file is selected via Drag & Drop or clicking
  const handleFileChange = async (selectedFile) => {
    if (!selectedFile) return;
    setFile(selectedFile);
    setIsUploading(true);
    setUploadProgress(0);
    setErrorMsg('');

    try {
      // Step 1: Request presigned URL from Backend (running on Port 8000)
      const filename = encodeURIComponent(selectedFile.name);
      const contentType = encodeURIComponent(selectedFile.type || 'application/pdf');
      
      const res = await fetch(`http://localhost:8000/api/v1/upload-url?filename=${filename}&content_type=${contentType}`);
      if (!res.ok) throw new Error('Failed to fetch temporary upload URL from backend');
      
      const { presigned_url, file_path } = await res.json();

      // Step 2: Upload file directly to S3 / MinIO
      // We use XMLHttpRequest instead of fetch to track progress smoothly
      const xhr = new XMLHttpRequest();
      xhr.open('PUT', presigned_url, true);
      xhr.setRequestHeader('Content-Type', selectedFile.type || 'application/pdf');

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percentComplete = Math.round((event.loaded / event.total) * 100);
          setUploadProgress(percentComplete);
        }
      };

      xhr.onload = () => {
        if (xhr.status === 200) {
          setUploadedFilePath(file_path);
          setIsUploading(false);
          setUploadProgress(100);
        } else {
          setErrorMsg('Object storage rejected direct file upload.');
          setIsUploading(false);
        }
      };

      xhr.onerror = () => {
        setErrorMsg('Network error uploading directly to object storage.');
        setIsUploading(false);
      };

      xhr.send(selectedFile);

    } catch (err) {
      console.error(err);
      setErrorMsg(err.message || 'File upload sequence failed.');
      setIsUploading(false);
    }
  };

  // Submit form data to start Phase-1 Analysis
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!uploadedFilePath) {
      setErrorMsg('Please upload a pitch deck first.');
      return;
    }
    
    setIsAnalyzing(true);
    setAnalysisResult(null);
    setErrorMsg('');

    try {
      const response = await fetch('http://localhost:8000/api/v1/analyze-investment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          file_path: uploadedFilePath,
          startup_name: startupName,
          industry_sector: sector,
          funding_stage: stage,
          requested_amount: parseFloat(amount) || 0
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Analysis execution failed.');
      }

      const result = await response.json();
      setAnalysisResult(result);
    } catch (err) {
      console.error(err);
      setErrorMsg(err.message || 'Error occurred while contacting pipeline service.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Reset page state
  const handleReset = () => {
    setStartupName('');
    setSector('Artificial Intelligence');
    setStage('SEED');
    setAmount('');
    setFile(null);
    setUploadProgress(0);
    setUploadedFilePath('');
    setAnalysisResult(null);
    setErrorMsg('');
  };

  return (
    <div className="app-container">
      {/* Branding Hero Banner */}
      <header className="app-header">
        <div className="app-title-badge">
          <Cpu size={14} /> Phase-1 Testing Environment
        </div>
        <h1>Automated VC Investment Analyst</h1>
        <p>A decoupled multi-container agent pipeline. Upload a deck to MinIO and trigger mock Phase-1 analysis with our LangGraph engine.</p>
      </header>

      {/* Main Content */}
      <div className="workspace-grid">
        
        {/* Input Panel Card */}
        <section className="panel-card">
          <h2 className="panel-card-title">
            <Zap size={20} className="empty-state-icon" style={{ color: 'var(--accent-indigo)' }} />
            Investment Intake Form
          </h2>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div className="form-group">
              <label className="form-label">Startup Name</label>
              <input 
                type="text" 
                className="form-input" 
                placeholder="e.g. Antigravity AI" 
                required 
                value={startupName}
                onChange={(e) => setStartupName(e.target.value)}
                disabled={isAnalyzing}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Sector</label>
              <select 
                className="form-input"
                value={sector}
                onChange={(e) => setSector(e.target.value)}
                disabled={isAnalyzing}
              >
                <option value="Artificial Intelligence">Artificial Intelligence</option>
                <option value="SaaS & DevTools">SaaS & DevTools</option>
                <option value="FinTech">FinTech</option>
                <option value="Web3 & Crypto">Web3 & Crypto</option>
                <option value="Biotech & Healthcare">Biotech & Healthcare</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Funding Stage</label>
              <select 
                className="form-input"
                value={stage}
                onChange={(e) => setStage(e.target.value)}
                disabled={isAnalyzing}
              >
                <option value="PRE_SEED">Pre-Seed</option>
                <option value="SEED">Seed</option>
                <option value="SERIES_A">Series A</option>
                <option value="SERIES_B">Series B</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Ask Amount ($ USD)</label>
              <input 
                type="number" 
                className="form-input" 
                placeholder="e.g. 1500000" 
                required
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                disabled={isAnalyzing}
              />
            </div>

            {/* Direct Upload Drag Zone */}
            <div className="form-group">
              <label className="form-label">Pitch Deck (PDF / PPTX)</label>
              <input 
                type="file" 
                style={{ display: 'none' }} 
                ref={fileInputRef} 
                accept=".pdf,.pptx"
                onChange={(e) => handleFileChange(e.target.files[0])}
              />
              
              {!file ? (
                <div className="file-dropzone" onClick={() => fileInputRef.current.click()}>
                  <div className="file-dropzone-icon">
                    <Upload size={20} />
                  </div>
                  <p style={{ fontWeight: '600', fontSize: '0.9rem', color: '#fff' }}>Click to select pitch deck</p>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Files uploaded securely to local MinIO</p>
                </div>
              ) : (
                <div className="file-upload-card">
                  <FileText size={24} style={{ color: 'var(--accent-indigo)' }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ fontSize: '0.85rem', fontWeight: '600', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                      {file.name}
                    </p>
                    {isUploading ? (
                      <div>
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Uploading direct to MinIO...</p>
                        <div className="progress-container">
                          <div className="progress-bar" style={{ width: `${uploadProgress}%` }}></div>
                        </div>
                      </div>
                    ) : uploadedFilePath ? (
                      <p style={{ fontSize: '0.75rem', color: 'var(--accent-green)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <CheckCircle size={12} /> Stored at MinIO path: {uploadedFilePath.slice(0, 20)}...
                      </p>
                    ) : null}
                  </div>
                </div>
              )}
            </div>

            {errorMsg && (
              <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', color: 'var(--accent-red)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem' }}>
                {errorMsg}
              </div>
            )}

            <button 
              type="submit" 
              className="btn-primary" 
              disabled={isUploading || isAnalyzing || !uploadedFilePath}
            >
              {isAnalyzing ? (
                <>
                  <Loader2 size={18} className="spinner" /> Analyzing Deck...
                </>
              ) : (
                'Run Investment Pipeline'
              )}
            </button>

            {analysisResult && (
              <button 
                type="button" 
                className="btn-primary" 
                style={{ background: 'transparent', border: '1px solid var(--border-glass)', boxShadow: 'none' }}
                onClick={handleReset}
              >
                Clear / Reset Form
              </button>
            )}
          </form>
        </section>

        {/* Dashboard Results Viewer */}
        <section className="panel-card" style={{ minHeight: '500px' }}>
          <h2 className="panel-card-title">
            <Layers size={20} className="empty-state-icon" style={{ color: 'var(--accent-purple)' }} />
            VC Analysis Dashboard
          </h2>

          {!analysisResult && !isAnalyzing ? (
            <div className="empty-state">
              <FileText size={64} className="empty-state-icon" />
              <h3>Awaiting Input</h3>
              <p>Fill out the investment form and upload a pitch deck. The multi-agent pipeline output will populate here once completed.</p>
            </div>
          ) : isAnalyzing ? (
            <div className="empty-state">
              <Loader2 size={64} className="spinner" style={{ color: 'var(--accent-indigo)' }} />
              <h3>Running Decoupled Pipeline</h3>
              <p style={{ maxWidth: '400px' }}>Intake Agent is retrieving PDF bytes from MinIO storage, executing Vision parsing, and coordinating agent nodes inside your LangGraph environment...</p>
              
              <div className="timeline" style={{ width: '100%', maxWidth: '450px', marginTop: '2rem' }}>
                <div className="timeline-item">
                  <span style={{ fontSize: '0.9rem', fontWeight: '500' }}>1. S3/MinIO File Intake</span>
                  <span className="status-indicator running">Active</span>
                </div>
                <div className="timeline-item">
                  <span style={{ fontSize: '0.9rem', fontWeight: '500', opacity: 0.5 }}>2. Company Profile Extractor</span>
                  <span className="status-indicator pending">Queued</span>
                </div>
                <div className="timeline-item">
                  <span style={{ fontSize: '0.9rem', fontWeight: '500', opacity: 0.5 }}>3. Market Research Agent</span>
                  <span className="status-indicator pending">Queued</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="report-grid">
              {/* Report Header Banner */}
              <div className="report-header-banner">
                <div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: '700' }}>{analysisResult.startup_name}</h3>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    Processed Deck: {analysisResult.metadata?.file_processed}
                  </p>
                </div>
                <span className="status-indicator success">
                  Pipeline Verified
                </span>
              </div>

              {/* Company Profiler Card */}
              <div className="metric-card">
                <div className="metric-header">
                  <Users size={14} /> Company Profile
                </div>
                <div className="metric-value">
                  {analysisResult.analysis?.company_profile?.sector || 'N/A'}
                </div>
                <div className="metric-desc">
                  <strong>Problem:</strong> {analysisResult.analysis?.company_profile?.problem_statement || 'Awaiting actual LLM extraction...'}
                  <br />
                  <strong>Solution:</strong> {analysisResult.analysis?.company_profile?.solution || 'Awaiting actual LLM extraction...'}
                </div>
              </div>

              {/* Market Dynamics Card */}
              <div className="metric-card">
                <div className="metric-header">
                  <TrendingUp size={14} /> Market Sizing (TAM)
                </div>
                <div className="metric-value" style={{ color: 'var(--accent-blue)' }}>
                  {analysisResult.analysis?.market_analysis?.tam?.value || '$100 Billion (Mocked)'}
                </div>
                <div className="metric-desc">
                  <strong>Growth Rate:</strong> {analysisResult.analysis?.market_analysis?.growth_rate || '35% YoY'}
                  <br />
                  <strong>Source:</strong> {analysisResult.analysis?.market_analysis?.tam?.source || 'Gartner'}
                </div>
              </div>

              {/* Team Extractor Card */}
              <div className="metric-card">
                <div className="metric-header">
                  <Activity size={14} /> Core Founders
                </div>
                <div className="metric-value" style={{ fontSize: '1.1rem' }}>
                  {analysisResult.analysis?.founders?.[0]?.name || 'Antigravity Agent (CTO)'}
                </div>
                <div className="metric-desc">
                  <strong>Bio:</strong> {analysisResult.analysis?.founders?.[0]?.bio_from_deck || 'AI assistant specialized in advanced engineering'}
                  <br />
                  <strong>Past Roles:</strong> {analysisResult.analysis?.founders?.[0]?.past_roles?.join(', ') || 'Staff Engineer at Google DeepMind'}
                </div>
              </div>

              {/* Investment Recommendation Card */}
              <div className="metric-card" style={{ border: '1px solid rgba(16, 185, 129, 0.25)', background: 'rgba(16, 185, 129, 0.02)' }}>
                <div className="metric-header" style={{ color: 'var(--accent-green)' }}>
                  <ShieldAlert size={14} /> Recommendation
                </div>
                <div className="metric-value" style={{ color: 'var(--accent-green)' }}>
                  PROCEED TO DEEP DIVE
                </div>
                <div className="metric-desc">
                  The mock pipeline indicates excellent alignment with current industry trends and founder credentials. Proceed to Stage 2 validation.
                </div>
              </div>

              {/* Agent Nodes Executed */}
              <div className="metric-card" style={{ gridColumn: '1 / -1' }}>
                <div className="metric-header">
                  <Cpu size={14} /> Decoupled Agent Orchestrator Logs
                </div>
                <div className="timeline" style={{ marginTop: '0.75rem' }}>
                  <div className="timeline-item">
                    <span>Intake Manager Agent</span>
                    <span className="status-indicator success">Success</span>
                  </div>
                  <div className="timeline-item">
                    <span>Vision PDF Extractor</span>
                    <span className="status-indicator success">Success</span>
                  </div>
                  <div className="timeline-item">
                    <span>Market & Sector Research Agent</span>
                    <span className="status-indicator success">Success</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </section>

      </div>
    </div>
  );
}
