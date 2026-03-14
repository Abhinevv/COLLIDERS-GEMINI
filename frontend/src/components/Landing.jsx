import { useEffect, useRef } from "react";
import "./landing.css";

function StarCanvas() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    let animId;

    // ── resize to fill viewport ──
    function resize() {
      canvas.width  = window.innerWidth;
      canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener("resize", resize);

    // ── star layers (3 depths for parallax feel) ──
    const layers = [
      { count: 160, speed: 0.012, rMin: 0.3, rMax: 0.8,  alpha: 0.45 }, // far
      { count:  80, speed: 0.025, rMin: 0.6, rMax: 1.2,  alpha: 0.60 }, // mid
      { count:  30, speed: 0.045, rMin: 0.9, rMax: 1.8,  alpha: 0.80 }, // near
    ];

    const stars = layers.flatMap(({ count, speed, rMin, rMax, alpha }) =>
      Array.from({ length: count }, () => ({
        x:      Math.random(),
        y:      Math.random(),
        r:      rMin + Math.random() * (rMax - rMin),
        alpha:  alpha * (0.6 + Math.random() * 0.4),
        speed,
        twinkleOffset: Math.random() * Math.PI * 2,
        twinkleSpeed:  0.4 + Math.random() * 0.8,
      }))
    );

    // ── occasional blue-tinted "deep space" stars ──
    const blueStars = Array.from({ length: 18 }, () => ({
      x:     Math.random(),
      y:     Math.random(),
      r:     0.8 + Math.random() * 1.0,
      alpha: 0.3 + Math.random() * 0.3,
      speed: 0.008,
      twinkleOffset: Math.random() * Math.PI * 2,
      twinkleSpeed:  0.3 + Math.random() * 0.5,
    }));

    let t = 0;

    function draw() {
      const W = canvas.width;
      const H = canvas.height;

      ctx.clearRect(0, 0, W, H);

      // White stars
      stars.forEach((s) => {
        s.y -= s.speed * 0.001;
        if (s.y < 0) { s.y = 1; s.x = Math.random(); }

        const tw = 0.75 + 0.25 * Math.sin(t * s.twinkleSpeed + s.twinkleOffset);
        ctx.beginPath();
        ctx.arc(s.x * W, s.y * H, s.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(210, 228, 255, ${s.alpha * tw})`;
        ctx.fill();
      });

      // Blue-tinted stars
      blueStars.forEach((s) => {
        s.y -= s.speed * 0.001;
        if (s.y < 0) { s.y = 1; s.x = Math.random(); }

        const tw = 0.6 + 0.4 * Math.sin(t * s.twinkleSpeed + s.twinkleOffset);

        // soft glow halo
        const grd = ctx.createRadialGradient(
          s.x * W, s.y * H, 0,
          s.x * W, s.y * H, s.r * 3
        );
        grd.addColorStop(0,   `rgba(100, 180, 255, ${s.alpha * tw})`);
        grd.addColorStop(1,   "transparent");
        ctx.beginPath();
        ctx.arc(s.x * W, s.y * H, s.r * 3, 0, Math.PI * 2);
        ctx.fillStyle = grd;
        ctx.fill();

        // core dot
        ctx.beginPath();
        ctx.arc(s.x * W, s.y * H, s.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(160, 210, 255, ${s.alpha * tw * 1.2})`;
        ctx.fill();
      });

      // Rare shooting star
      if (Math.random() < 0.0008) {
        const sx = Math.random() * W;
        const sy = Math.random() * H * 0.5;
        const len = 60 + Math.random() * 80;
        const grd = ctx.createLinearGradient(sx, sy, sx + len, sy + len * 0.3);
        grd.addColorStop(0,   "rgba(180, 220, 255, 0)");
        grd.addColorStop(0.3, "rgba(180, 220, 255, 0.55)");
        grd.addColorStop(1,   "rgba(180, 220, 255, 0)");
        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.lineTo(sx + len, sy + len * 0.3);
        ctx.strokeStyle = grd;
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      t += 0.016;
      animId = requestAnimationFrame(draw);
    }

    draw();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return <canvas ref={canvasRef} className="stars-canvas" />;
}

export default function Landing({ onStart }) {
  return (
    <div className="landing-page">

      {/* ── ANIMATED STAR BACKGROUND ── */}
      <StarCanvas />

      <div className="landing-inner">

        {/* ── HERO ── */}
        <section className="hero-section">
          <div className="hero-eyebrow">
            <span className="hero-eyebrow-dot" />
            Orbital Safety Platform
          </div>

          <h1>COLLIDERS</h1>
          <h2>Space Debris Tracking &amp; Collision Avoidance System</h2>

          <p className="hero-description">
            An advanced satellite safety platform designed to track orbital
            debris, analyze collision risks, and assist operators in preventing
            catastrophic space collisions using real-time orbital data and
            scientific probability models.
          </p>

          <button className="start-button" onClick={onStart}>
            Launch Dashboard
          </button>
        </section>

        <div className="hero-divider" />

        {/* ── STATS ── */}
        <section className="stats-section">
          <div className="section-header">
            <span className="section-label">System Coverage</span>
            <h2>Live Tracking Numbers</h2>
          </div>

          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-number">74</span>
              <p>Satellites Tracked</p>
            </div>
            <div className="stat-card">
              <span className="stat-number">725+</span>
              <p>Debris Objects</p>
            </div>
            <div className="stat-card">
              <span className="stat-number">628K+</span>
              <p>Collision Scenarios</p>
            </div>
            <div className="stat-card">
              <span className="stat-number">NASA</span>
              <p>Probability Models</p>
            </div>
          </div>
        </section>

        {/* ── FEATURES ── */}
        <section className="features-section">
          <div className="section-header">
            <span className="section-label">Capabilities</span>
            <h2>Core Features</h2>
          </div>

          <div className="features-grid">
            <div className="feature-card">
              <span className="feature-icon">📡</span>
              <h3>Real-Time Debris Tracking</h3>
              <p>Tracks orbital debris using Space-Track TLE data with live updates.</p>
            </div>
            <div className="feature-card">
              <span className="feature-icon">🎯</span>
              <h3>Collision Probability Analysis</h3>
              <p>Monte-Carlo simulations calculate realistic collision risk.</p>
            </div>
            <div className="feature-card">
              <span className="feature-icon">⚠️</span>
              <h3>Risk Ranking</h3>
              <p>Ranks debris threats based on probability and impact severity.</p>
            </div>
            <div className="feature-card">
              <span className="feature-icon">🛰️</span>
              <h3>Satellite Risk Profiles</h3>
              <p>Detailed safety analysis for each monitored satellite.</p>
            </div>
            <div className="feature-card">
              <span className="feature-icon">🔔</span>
              <h3>Automated Alerts</h3>
              <p>Real-time warnings for high-risk collision scenarios.</p>
            </div>
          </div>
        </section>

        {/* ── WORKFLOW ── */}
        <section className="workflow-section">
          <div className="section-header">
            <span className="section-label">Process</span>
            <h2>How It Works</h2>
          </div>

          <div className="workflow-grid">
            <div className="workflow-step">
              <div className="workflow-step-number">01</div>
              <div className="workflow-step-content">
                <h3>Fetch Orbital Data</h3>
                <p>Satellite and debris orbital elements retrieved from Space-Track using TLE datasets.</p>
              </div>
            </div>
            <div className="workflow-step">
              <div className="workflow-step-number">02</div>
              <div className="workflow-step-content">
                <h3>Orbit Propagation</h3>
                <p>SGP4 propagation predicts future satellite positions and trajectories.</p>
              </div>
            </div>
            <div className="workflow-step">
              <div className="workflow-step-number">03</div>
              <div className="workflow-step-content">
                <h3>Collision Simulation</h3>
                <p>Monte-Carlo simulations evaluate potential collision scenarios.</p>
              </div>
            </div>
            <div className="workflow-step">
              <div className="workflow-step-number">04</div>
              <div className="workflow-step-content">
                <h3>Risk Classification</h3>
                <p>Results categorized into LOW, MODERATE, HIGH, and CRITICAL threat levels.</p>
              </div>
            </div>
          </div>
        </section>

        {/* ── TECH STACK ── */}
        <section className="tech-section">
          <div className="section-header">
            <span className="section-label">Built With</span>
            <h2>Tech Stack</h2>
          </div>

          <div className="tech-grid">
            <div className="tech-card">
              <span className="tech-icon">🐍</span>
              <h3>Python</h3>
              <p>Core logic</p>
            </div>
            <div className="tech-card">
              <span className="tech-icon">🛸</span>
              <h3>SGP4</h3>
              <p>Orbit propagation</p>
            </div>
            <div className="tech-card">
              <span className="tech-icon">🔢</span>
              <h3>NumPy / SciPy</h3>
              <p>Mathematical computations</p>
            </div>
            <div className="tech-card">
              <span className="tech-icon">🌐</span>
              <h3>Plotly / CesiumJS</h3>
              <p>3D visualization</p>
            </div>
            <div className="tech-card">
              <span className="tech-icon">🎲</span>
              <h3>Monte Carlo</h3>
              <p>Risk simulation</p>
            </div>
            <div className="tech-card">
              <span className="tech-icon">🧬</span>
              <h3>Genetic Algorithms</h3>
              <p>Maneuver optimization</p>
            </div>
          </div>
        </section>

        {/* ── FOOTER ── */}
        <footer className="landing-footer">
          <p>COLLIDERS — Making Space Safer Through Intelligent Collision Avoidance</p>
          <button className="start-button" onClick={onStart}>
            Get Started
          </button>
        </footer>

      </div>
    </div>
  );
}