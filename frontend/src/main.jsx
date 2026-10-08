const { useState, useEffect } = window.React;
const { createRoot } = window.ReactDOM;

const PIPELINE_STEPS = [
  { id: 1, name: "Resume", desc: "Resume Ingestion" },
  { id: 2, name: "Job Search", desc: "Multi-Source Fetch" },
  { id: 3, name: "URL Validation", desc: "Link Verification" },
  { id: 4, name: "Remove Invalid", desc: "Dead Link Removal" },
  { id: 5, name: "Deduplication", desc: "Cross-Platform Merge" },
  { id: 6, name: "Skill Extraction", desc: "Profile Ontology" },
  { id: 7, name: "Job Matching", desc: "TF-IDF Alignment" },
  { id: 8, name: "Match Score", desc: "Composite Scoring" },
  { id: 9, name: "Job Ranking", desc: "Relevance Ordering" },
  { id: 10, name: "Original URL", desc: "Apply Link" },
  { id: 11, name: "Skill Gap", desc: "Market Gap Analysis" },
  { id: 12, name: "Trending Tech", desc: "Industry Demand" },
  { id: 13, name: "Roadmap", desc: "4-Phase Growth Plan" }
];

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(() => {
    try {
      return localStorage.getItem('careermatch-auth') === 'true';
    } catch {
      return false;
    }
  });
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      return localStorage.getItem('careermatch-user') || 'Applicant';
    } catch {
      return 'Applicant';
    }
  });
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [loginError, setLoginError] = useState('');
  const [activeTab, setActiveTab] = useState('jobs');
  const [loading, setLoading] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  // Input States
  const [resumeText, setResumeText] = useState('');
  const [resumeFile, setResumeFile] = useState(null);
  const [targetRole, setTargetRole] = useState('Full Stack Software Engineer');
  const [location, setLocation] = useState('Remote');
  const [sources, setSources] = useState({
    'Remote OK': true,
    Adzuna: true,
    'The Muse': true
  });

  // Data States
  const [candidateProfile, setCandidateProfile] = useState(null);
  const [validationAudit, setValidationAudit] = useState(null);
  const [rankedJobs, setRankedJobs] = useState([]);
  const [skillGapData, setSkillGapData] = useState(null);
  const [trendingTechList, setTrendingTechList] = useState([]);
  const [careerRoadmap, setCareerRoadmap] = useState(null);

  // Filter States
  const [minScoreFilter, setMinScoreFilter] = useState(40);
  const [sourceFilter, setSourceFilter] = useState('all');
  const [sampleResumes, setSampleResumes] = useState({});

  // Fetch sample resumes on initial mount
  useEffect(() => {
    fetch('/api/jobs/sample-resumes')
      .then(res => res.json())
      .then(data => {
        setSampleResumes(data);
        if (data.frontend && !resumeText) {
          setResumeText(data.frontend);
        }
      })
      .catch(() => {
        // Fallback default sample
        setResumeText(`Alex Morgan\nalex.morgan@example.dev | (555) 234-5678\nSkills: JavaScript, TypeScript, React, Tailwind CSS, Next.js, Redux, REST APIs, Git, Jest\nExperience: 3 years building responsive web apps with React and TypeScript.`);
      });
  }, []);

  const toggleSource = (sourceName) => {
    setSources(prev => ({ ...prev, [sourceName]: !prev[sourceName] }));
  };

  const handleLogin = (event) => {
    event.preventDefault();
    const email = loginForm.email.trim();
    const password = loginForm.password.trim();

    if (!email || !/\S+@\S+\.\S+/.test(email) || !password || password.length < 6) {
      setLoginError('Enter a valid email and a password with at least 6 characters.');
      return;
    }

    try {
      localStorage.setItem('careermatch-auth', 'true');
      localStorage.setItem('careermatch-user', email);
    } catch (err) {
      console.warn('Unable to persist auth state:', err);
    }

    setCurrentUser(email.split('@')[0]);
    setIsLoggedIn(true);
    setLoginError('');
    setLoginForm({ email: '', password: '' });
  };

  const handleLogout = () => {
    try {
      localStorage.removeItem('careermatch-auth');
      localStorage.removeItem('careermatch-user');
    } catch (err) {
      console.warn('Unable to clear auth state:', err);
    }

    setIsLoggedIn(false);
    setLoginForm({ email: '', password: '' });
    setLoginError('');
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setResumeFile(file);
      if (file.name.endsWith('.txt')) {
        const reader = new FileReader();
        reader.onload = (event) => setResumeText(event.target.result);
        reader.readAsText(file);
      } else {
        setResumeText(`[Attached file: ${file.name}]`);
      }
    }
  };

  const loadSample = (key) => {
    if (sampleResumes[key]) {
      setResumeFile(null);
      setResumeText(sampleResumes[key]);
      if (key === 'frontend') setTargetRole('Frontend React Developer');
      if (key === 'backend') setTargetRole('Python Backend Engineer');
      if (key === 'ai_ml') setTargetRole('Machine Learning / AI Engineer');
    }
  };

  const runPipeline = async () => {
    setLoading(true);
    setCurrentStepIndex(1);

    const formData = new FormData();
    if (resumeFile) {
      formData.append('resume_file', resumeFile);
    } else {
      formData.append('resume_text', resumeText);
    }
    formData.append('target_role', targetRole);
    formData.append('location', location);
    
    const activeSourcesList = Object.keys(sources).filter(k => sources[k]).join(',');
    formData.append('sources', activeSourcesList);

    const stepInterval = setInterval(() => {
      setCurrentStepIndex(prev => (prev < 12 ? prev + 1 : prev));
    }, 35);

    try {
      const response = await fetch('/api/career/pipeline', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      clearInterval(stepInterval);
      setCurrentStepIndex(13);

      if (response.ok) {
        setCandidateProfile(data.candidate_profile);
        setValidationAudit(data.validation_audit);
        setRankedJobs(data.ranked_jobs || []);
        setSkillGapData(data.skill_gap_analysis);
        setTrendingTechList(data.trending_technologies || []);
        setCareerRoadmap(data.career_roadmap);
      } else {
        alert(data.detail || "Error processing pipeline");
      }
    } catch (err) {
      clearInterval(stepInterval);
      alert("Network error: Please ensure FastAPI backend is running.");
    } finally {
      setLoading(false);
    }
  };

  // Filtered jobs
  const filteredJobs = rankedJobs.filter(job => {
    const meetsScore = job.match_score >= minScoreFilter;
    const meetsSource = sourceFilter === 'all' || job.source.toLowerCase().includes(sourceFilter.toLowerCase());
    return meetsScore && meetsSource;
  });

  if (!isLoggedIn) {
    return (
      <div className="login-shell">
        <div className="login-panel">
          <div className="login-visual">
            <div className="brand-logo login-brand-logo">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
              </svg>
            </div>
            <span className="login-overline">CareerMatch AI</span>
            <h1>Job matching, validation, and growth strategy in one place.</h1>
            <ul className="login-points">
              <li>Multi-source job aggregation</li>
              <li>Resume-to-role match scoring</li>
              <li>Skill gap and roadmap guidance</li>
            </ul>
          </div>

          <div className="login-form-wrap">
            <div className="login-badge">Secure Access</div>
            <h2>Welcome back</h2>
            <p className="login-subtitle">Sign in to continue building your next move.</p>

            <form className="login-form" onSubmit={handleLogin}>
              <label className="login-field">
                <span>Email</span>
                <input
                  type="email"
                  className="login-input"
                  value={loginForm.email}
                  onChange={(e) => setLoginForm(prev => ({ ...prev, email: e.target.value }))}
                  placeholder="name@company.com"
                />
              </label>

              <label className="login-field">
                <span>Password</span>
                <input
                  type="password"
                  className="login-input"
                  value={loginForm.password}
                  onChange={(e) => setLoginForm(prev => ({ ...prev, password: e.target.value }))}
                  placeholder="••••••••"
                />
              </label>

              {loginError && <div className="login-error">{loginError}</div>}

              <button type="submit" className="btn-primary login-submit">
                Sign In
              </button>
            </form>

            <div className="login-footer">
              <span>Demo access</span>
              <strong>candidate@careermatch.ai / password123</strong>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* App Header */}
      <header className="app-header">
        <div className="brand-section">
          <div className="brand-logo">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <h1 className="brand-title">CareerMatch AI</h1>
              <span className="brand-badge">Pipeline Engine</span>
            </div>
            <p className="brand-subtitle">
              Automated multi-source matching, URL validation, skill gap analysis &amp; personalized career roadmap
            </p>
          </div>
        </div>

        <div className="header-right">
          <div className="header-sources">
            <span style={{ fontWeight: 600, color: '#e2e8f0', marginRight: 4 }}>Job Sources:</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span className="source-dot remoteok"></span> Remote OK
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span className="source-dot adzuna"></span> Adzuna
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span className="source-dot muse"></span> The Muse
            </span>
          </div>

          <div className="user-menu">
            <span className="user-pill">Hi, {currentUser}</span>
            <button className="logout-btn" onClick={handleLogout}>Log out</button>
          </div>
        </div>
      </header>

      {/* 13-Step Pipeline Flow Stepper */}
      <section className="pipeline-stepper">
        <div className="stepper-header">
          <span className="stepper-title">Proposed Architecture Pipeline</span>
          <span className="stepper-status">
            {loading ? (
              <>
                <span className="spinner"></span>
                Processing: {PIPELINE_STEPS[currentStepIndex - 1]?.desc || "Analyzing..."}
              </>
            ) : candidateProfile ? (
              <span style={{ color: 'var(--success)' }}>✓ Pipeline Complete</span>
            ) : (
              <span>Ready to Execute</span>
            )}
          </span>
        </div>

        <div className="stepper-flow">
          {PIPELINE_STEPS.map((step, idx) => {
            const isCompleted = currentStepIndex > step.id || (candidateProfile && !loading);
            const isActive = loading && currentStepIndex === step.id;
            return (
              <React.Fragment key={step.id}>
                <div className={`step-node ${isCompleted ? 'completed' : ''} ${isActive ? 'active' : ''}`}>
                  <div className="step-circle">
                    {isCompleted ? '✓' : step.id}
                  </div>
                  <span className="step-label">{step.name}</span>
                </div>
                {idx < PIPELINE_STEPS.length - 1 && (
                  <div className={`step-connector ${isCompleted ? 'completed' : ''}`}></div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </section>

      {/* Control Deck: Resume & Search Inputs */}
      <div className="control-deck">
        {/* Card 1: Resume Upload & Parsing */}
        <div className="card">
          <h2 className="card-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
            </svg>
            Candidate Resume
          </h2>
          <p className="card-desc">
            Upload your resume (.pdf, .docx, .txt) or paste text to extract technical skills &amp; experience.
          </p>

          <div className="sample-profiles">
            <span className="sample-label">Try Demo:</span>
            <button className="sample-btn" onClick={() => loadSample('frontend')}>Frontend React</button>
            <button className="sample-btn" onClick={() => loadSample('backend')}>Python Backend</button>
            <button className="sample-btn" onClick={() => loadSample('ai_ml')}>AI / ML Engineer</button>
          </div>

          <label className="upload-zone">
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
            <div className="upload-icon">
              <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
              </svg>
            </div>
            <div className="upload-text">
              {resumeFile ? resumeFile.name : "Click to select or drag & drop resume"}
            </div>
            <div className="upload-sub">PDF, DOCX, or plain text supported</div>
          </label>

          <textarea
            className="resume-textarea"
            placeholder="Or paste resume text here..."
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
          />

          {candidateProfile && (
            <div className="extracted-profile">
              <div className="profile-meta">
                <span className="candidate-name">{candidateProfile.name}</span>
                <span className="experience-tag">{candidateProfile.years_of_experience}+ Years Exp</span>
              </div>
              <div className="skills-cloud">
                {candidateProfile.skills.map(sk => (
                  <span key={sk} className="skill-chip">{sk}</span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Card 2: Job Aggregator & Search Settings */}
        <div className="card">
          <h2 className="card-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            Multi-Source Target Roles
          </h2>
          <p className="card-desc">
            Aggregates live opportunities from Remote OK, Adzuna, and The Muse with automatic verification.
          </p>

          <div className="form-group">
            <label className="form-label">Target Role / Keywords</label>
            <input
              type="text"
              className="form-input"
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              placeholder="e.g. Senior Full Stack Engineer, Frontend Developer"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Preferred Location</label>
            <input
              type="text"
              className="form-input"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. Remote, San Francisco, New York"
            />
          </div>

          <label className="form-label">Active Job Portals to Search &amp; Deduplicate</label>
          <div className="sources-selector">
            {['Remote OK', 'Adzuna', 'The Muse'].map(src => (
              <label key={src} className="source-checkbox-label">
                <input
                  type="checkbox"
                  checked={sources[src]}
                  onChange={() => toggleSource(src)}
                />
                {src}
              </label>
            ))}
          </div>

          <button
            className="btn-primary"
            onClick={runPipeline}
            disabled={loading || (!resumeText.trim() && !resumeFile)}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Running CareerMatch AI Pipeline...
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polygon points="5 3 19 12 5 21 5 3"></polygon>
                </svg>
                Run CareerMatch AI Pipeline
              </>
            )}
          </button>
        </div>
      </div>

      {/* Metrics Banner (Visible after audit) */}
      {validationAudit && (
        <section className="metrics-banner">
          <div className="metric-card">
            <span className="metric-val indigo">{validationAudit.initial_count}</span>
            <span className="metric-name">Raw Postings Fetched</span>
          </div>
          <div className="metric-card">
            <span className="metric-val red">-{validationAudit.invalid_urls_removed_count}</span>
            <span className="metric-name">Invalid / Dead URLs</span>
          </div>
          <div className="metric-card">
            <span className="metric-val orange">-{validationAudit.expired_removed_count}</span>
            <span className="metric-name">Expired Listings Filtered</span>
          </div>
          <div className="metric-card">
            <span className="metric-val cyan">-{validationAudit.duplicates_removed_count}</span>
            <span className="metric-name">Duplicates Merged</span>
          </div>
          <div className="metric-card">
            <span className="metric-val green">{validationAudit.final_valid_count}</span>
            <span className="metric-name">Active Verified Jobs</span>
          </div>
        </section>
      )}

      {/* Navigation Tabs */}
      <nav className="tabs-nav">
        <button
          className={`tab-btn ${activeTab === 'jobs' ? 'active' : ''}`}
          onClick={() => setActiveTab('jobs')}
        >
          <span>🎯 Ranked Job Matches</span>
          {rankedJobs.length > 0 && <span className="tab-badge">{filteredJobs.length}</span>}
        </button>

        <button
          className={`tab-btn ${activeTab === 'skills' ? 'active' : ''}`}
          onClick={() => setActiveTab('skills')}
        >
          <span>📊 Skill Gap Analysis</span>
          {skillGapData && (
            <span className="tab-badge">{skillGapData.critical_gaps_count} Critical</span>
          )}
        </button>

        <button
          className={`tab-btn ${activeTab === 'trending' ? 'active' : ''}`}
          onClick={() => setActiveTab('trending')}
        >
          <span>🔥 Trending Technologies</span>
          {trendingTechList.length > 0 && <span className="tab-badge">{trendingTechList.length}</span>}
        </button>

        <button
          className={`tab-btn ${activeTab === 'roadmap' ? 'active' : ''}`}
          onClick={() => setActiveTab('roadmap')}
        >
          <span>🗺️ Career Improvement Roadmap</span>
          {careerRoadmap && (
            <span className="tab-badge" style={{ color: 'var(--success)' }}>
              +{careerRoadmap.score_boost}% Boost
            </span>
          )}
        </button>
      </nav>

      {/* TAB 1: Ranked Job Matches */}
      {activeTab === 'jobs' && (
        <div>
          {rankedJobs.length > 0 && (
            <div className="filter-bar">
              <div className="filter-group">
                <span className="filter-label">Min Match Score: {minScoreFilter}%</span>
                <input
                  type="range"
                  min="0"
                  max="95"
                  step="5"
                  value={minScoreFilter}
                  onChange={(e) => setMinScoreFilter(Number(e.target.value))}
                  className="filter-slider"
                />
              </div>

              <div className="filter-group">
                <span className="filter-label">Source Filter:</span>
                <select
                  value={sourceFilter}
                  onChange={(e) => setSourceFilter(e.target.value)}
                  className="form-input"
                  style={{ padding: '6px 12px', fontSize: '0.8rem', width: 'auto' }}
                >
                  <option value="all">All Sources</option>
                  <option value="Remote OK">Remote OK</option>
                  <option value="Adzuna">Adzuna</option>
                  <option value="The Muse">The Muse</option>
                </select>
              </div>

              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Showing {filteredJobs.length} of {rankedJobs.length} opportunities
              </span>
            </div>
          )}

          {filteredJobs.length > 0 ? (
            <div className="jobs-list">
              {filteredJobs.map((job) => {
                const scoreClass = job.match_score >= 75 ? 'high' : job.match_score >= 50 ? 'medium' : 'low';
                const platformClass = job.source.toLowerCase().includes('remote ok') || job.source.toLowerCase().includes('remoteok')
                  ? 'remoteok'
                  : job.source.toLowerCase().includes('adzuna')
                  ? 'adzuna'
                  : 'themuse';

                return (
                  <article key={job.id} className="job-card">
                    <div className="job-card-top">
                      <div className="job-main-info">
                        <div className="job-title-row">
                          <h3 className="job-title">{job.title}</h3>
                          <span className={`platform-tag ${platformClass}`}>
                            {job.source}
                          </span>
                        </div>
                        <div className="job-meta-row">
                          <span className="meta-item">🏢 {job.company}</span>
                          <span className="meta-item">📍 {job.location}</span>
                          <span className="meta-item">💼 {job.experience_level}</span>
                          <span className="meta-item">💰 {job.salary_range}</span>
                          <span className="meta-item">📅 {job.posted_date}</span>
                        </div>
                      </div>

                      <div className="score-badge-wrapper">
                        <div className={`match-score-badge ${scoreClass}`}>
                          <span>{job.match_score}%</span>
                        </div>
                        <span className="score-level-text" style={{ color: scoreClass === 'high' ? 'var(--success)' : scoreClass === 'medium' ? 'var(--warning)' : 'var(--danger)' }}>
                          {job.match_level}
                        </span>
                      </div>
                    </div>

                    <p className="job-desc">{job.description}</p>

                    <div className="skills-comparison">
                      <div>
                        <div className="skills-group-title matched">
                          ✓ Matched Skills ({job.matched_skills.length})
                        </div>
                        <div className="tag-list">
                          {job.matched_skills.map(sk => (
                            <span key={sk} className="tag-matched">{sk}</span>
                          ))}
                          {job.matched_skills.length === 0 && (
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>None matched directly</span>
                          )}
                        </div>
                      </div>

                      <div>
                        <div className="skills-group-title missing">
                          + Missing Skill Requirements ({job.missing_skills.length})
                        </div>
                        <div className="tag-list">
                          {job.missing_skills.map(sk => (
                            <span key={sk} className="tag-missing">{sk}</span>
                          ))}
                          {job.missing_skills.length === 0 && (
                            <span style={{ fontSize: '0.75rem', color: 'var(--success)' }}>All requirements met!</span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="job-actions">
                      <div className="verified-pill">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                          <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                        URL Checked &amp; Active
                      </div>

                      <a
                        href={job.original_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="apply-btn"
                      >
                        Apply on {job.source.split(',')[0]}
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <line x1="7" y1="17" x2="17" y2="7"></line>
                          <polyline points="7 7 17 7 17 17"></polyline>
                        </svg>
                      </a>
                    </div>
                  </article>
                );
              })}
            </div>
          ) : (
            <div className="empty-state card">
              <div className="empty-icon">🔍</div>
              <h3>No Jobs to Display</h3>
              <p>Upload a resume and click <strong>"Run CareerMatch AI Pipeline"</strong> to aggregate, validate, and rank matched positions.</p>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Skill Gap Analysis */}
      {activeTab === 'skills' && (
        <div>
          {skillGapData ? (
            <div className="gap-grid">
              <div className="readiness-meter-card">
                <h3>Market Readiness</h3>
                <div className="meter-circle">
                  <span className="meter-num">{skillGapData.market_readiness_index}%</span>
                  <span className="meter-caption">Readiness</span>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  Evaluated across {skillGapData.total_analyzed_jobs} active roles in {targetRole}.
                </p>

                <div style={{ marginTop: 24, textAlign: 'left' }}>
                  <h4 style={{ fontSize: '0.85rem', marginBottom: 8, color: 'var(--text-primary)' }}>Possessed Strengths:</h4>
                  <div className="tag-list">
                    {skillGapData.candidate_strengths.map(st => (
                      <span key={st.skill} className="tag-matched" title={st.market_presence}>
                        {st.skill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="gap-cards-container">
                <h3 style={{ fontSize: '1.1rem', marginBottom: 4 }}>
                  Skill Gaps &amp; Priority Remediation
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 12 }}>
                  Identified skills frequently demanded by employers for {targetRole} that are currently missing from your resume.
                </p>

                {skillGapData.missing_skills.map((item) => (
                  <div key={item.skill} className={`gap-card ${item.importance.toLowerCase()}`}>
                    <div>
                      <div className="gap-skill-name">{item.skill}</div>
                      <div className="gap-skill-action">{item.recommended_action}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span className={`gap-pill ${item.importance.toLowerCase()}`}>
                        {item.importance} Gap ({item.demand_percentage}% Demand)
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="empty-state card">
              <div className="empty-icon">📊</div>
              <h3>Skill Gap Data Not Ready</h3>
              <p>Execute the CareerMatch AI pipeline to extract your skills and analyze market gaps.</p>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: Trending Technologies */}
      {activeTab === 'trending' && (
        <div>
          <div style={{ marginBottom: 20 }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: 4 }}>
              Industry Trending Technologies &amp; In-Demand Stacks
            </h2>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
              Technologies seeing rapid adoption across hiring companies for modern engineering roles.
            </p>
          </div>

          <div className="trending-grid">
            {trendingTechList.map((item) => (
              <div key={item.name} className="trend-card">
                <div className="trend-header">
                  <h3 className="trend-name">{item.name}</h3>
                  <span className="trend-category">{item.category}</span>
                </div>

                <div className="trend-metrics">
                  <span className="growth-badge">📈 {item.growth_rate}</span>
                  <span style={{ color: 'var(--text-muted)' }}>•</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{item.market_demand}</span>
                </div>

                <p className="trend-reason">{item.strategic_reason}</p>

                <div className="trend-meta">
                  <span>Difficulty: <strong>{item.learning_difficulty}</strong></span>
                  <span>Est: <strong>{item.est_learning_time}</strong></span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 4: Career Improvement Roadmap */}
      {activeTab === 'roadmap' && (
        <div>
          {careerRoadmap ? (
            <div className="roadmap-container">
              {/* Summary & Score Projection Box */}
              <div className="roadmap-summary-box">
                <div className="roadmap-summary-text">
                  <h3 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 8, color: '#fff' }}>
                    Personalized Career Improvement Roadmap
                  </h3>
                  <p style={{ fontSize: '0.9rem', color: '#cbd5e1', lineHeight: 1.5 }}>
                    {careerRoadmap.summary}
                  </p>
                </div>

                <div className="roadmap-boost-badge">
                  <div className="boost-number">+{careerRoadmap.score_boost}%</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Match Score Trajectory: <strong>{careerRoadmap.current_match_score}% → {careerRoadmap.projected_match_score}%</strong>
                  </div>
                </div>
              </div>

              {/* 4-Phase Timeline */}
              <div className="roadmap-timeline">
                {careerRoadmap.phases.map((phase) => (
                  <div key={phase.phase_number} className="phase-card">
                    <div className="phase-header">
                      <h4 className="phase-title">{phase.title}</h4>
                      <span className="phase-duration">{phase.duration}</span>
                    </div>

                    <div className="phase-skills-row">
                      {phase.focus_skills.map(sk => (
                        <span key={sk} className="skill-chip">{sk}</span>
                      ))}
                    </div>

                    <div style={{ marginBottom: 12 }}>
                      <div className="phase-section-title">Core Learning Objectives</div>
                      <ul className="phase-list">
                        {phase.learning_objectives.map((obj, i) => (
                          <li key={i}>{obj}</li>
                        ))}
                      </ul>
                    </div>

                    <div style={{ marginBottom: 14 }}>
                      <div className="phase-section-title">Practical Activities &amp; Sandbox Tasks</div>
                      <ul className="phase-list">
                        {phase.practical_activities.map((act, i) => (
                          <li key={i}>{act}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="milestone-badge">
                      🏆 <strong>Milestone:</strong> {phase.milestone_project}
                    </div>
                  </div>
                ))}
              </div>

              {/* Flagship Portfolio Project Recommendation */}
              <div className="portfolio-box">
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: 6 }}>
                  Recommended Flagship Portfolio Project
                </h3>
                <h4 style={{ color: 'var(--accent-secondary)', fontSize: '1rem', marginBottom: 10 }}>
                  {careerRoadmap.recommended_portfolio_project.title}
                </h4>
                <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginBottom: 14 }}>
                  {careerRoadmap.recommended_portfolio_project.description}
                </p>

                <div style={{ marginBottom: 14 }}>
                  <span className="phase-section-title">Recommended Stack:</span>
                  <div className="tag-list" style={{ marginTop: 4 }}>
                    {careerRoadmap.recommended_portfolio_project.tech_stack.map(tech => (
                      <span key={tech} className="skill-chip">{tech}</span>
                    ))}
                  </div>
                </div>

                <div>
                  <span className="phase-section-title">Key Architectural Features to Demonstrate:</span>
                  <ul className="phase-list" style={{ marginTop: 4 }}>
                    {careerRoadmap.recommended_portfolio_project.key_features.map((feat, i) => (
                      <li key={i}>{feat}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Technical Interview Preparation Tips */}
              <div className="card">
                <h3 className="card-title">
                  <span>💡</span> Strategic Interview Preparation Tips
                </h3>
                <ul className="phase-list" style={{ marginTop: 8 }}>
                  {careerRoadmap.interview_preparation_tips.map((tip, i) => (
                    <li key={i} style={{ fontSize: '0.9rem', marginBottom: 8 }}>{tip}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <div className="empty-state card">
              <div className="empty-icon">🗺️</div>
              <h3>Roadmap Not Generated</h3>
              <p>Run the pipeline to receive a customized 4-phase career acceleration plan.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const rootElement = document.getElementById('root');
if (rootElement) {
  createRoot(rootElement).render(<App />);
}
