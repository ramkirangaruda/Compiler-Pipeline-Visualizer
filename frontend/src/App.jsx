import React, { useEffect, useState } from 'react';
import { NavLink, Route, Routes, useLocation, Link } from 'react-router-dom';
import ClickSpark from './reactbits/ClickSpark.jsx';
import Home from './pages/Home.jsx';
import Studio from './pages/Studio.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Dataset from './pages/Dataset.jsx';
import Architecture from './pages/Architecture.jsx';
import { api } from './api.js';

function Logo() {
  return (
    <Link to="/" className="logo" aria-label="Compiler Pipeline Visualizer home">
      <svg viewBox="0 0 64 64" aria-hidden="true">
        <circle cx="14" cy="32" r="7" fill="#fff" />
        <circle cx="32" cy="16" r="7" fill="#E7D623" />
        <circle cx="50" cy="32" r="7" fill="#2CF7A4" />
        <circle cx="32" cy="48" r="7" fill="#fff" />
        <path d="M19 27l8-7M37 21l8 7M45 37l-8 7M27 43l-8-7" stroke="#fff" strokeWidth="3.5" strokeLinecap="round" />
      </svg>
      <span className="logo-text"><span>COMPILER</span><span>PIPELINE</span></span>
    </Link>
  );
}

function Nav({ health }) {
  const links = [['/studio', 'Studio'], ['/dashboard', 'Dashboard'], ['/dataset', 'Dataset'], ['/architecture', 'Architecture']];
  return (
    <header className="nav">
      <div className="container nav-inner">
        <Logo />
        <nav className="nav-links" aria-label="Main">
          {links.map(([to, label]) => (
            <NavLink key={to} to={to} className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>{label}</NavLink>
          ))}
        </nav>
        <div className="nav-status" title="Backend connection and ML model status">
          <span className={`dot ${health ? 'on' : 'off'}`} />
          {health ? (health.model_loaded ? `API online · ${health.model}` : 'API online · no model') : 'API offline'}
        </div>
      </div>
    </header>
  );
}

function ScrollTop() {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return null;
}

export default function App() {
  const [health, setHealth] = useState(null);
  useEffect(() => {
    let alive = true;
    const ping = () => api.health().then((h) => alive && setHealth(h)).catch(() => alive && setHealth(null));
    ping();
    const t = setInterval(ping, 15000);
    return () => { alive = false; clearInterval(t); };
  }, []);

  return (
    <ClickSpark sparkColor="#E7D623" sparkSize={11} sparkRadius={22} sparkCount={9} duration={450}>
      <ScrollTop />
      <Nav health={health} />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/studio" element={<Studio />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/dataset" element={<Dataset />} />
          <Route path="/architecture" element={<Architecture />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </main>
      <footer className="footer">
        <div className="container footer-inner">
          <span>Compiler Design project · MiniC compiler + ML-assisted error repair</span>
          <span>UI components from <a href="https://reactbits.dev" target="_blank" rel="noreferrer">React Bits</a> · palette inspired by Yudu Robotics</span>
        </div>
      </footer>
    </ClickSpark>
  );
}
