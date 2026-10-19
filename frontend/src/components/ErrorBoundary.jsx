import React from 'react';

/** Keeps a failing visual widget (e.g. WebGL) from taking the whole page down. */
export default class ErrorBoundary extends React.Component {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(err) {
    console.warn('Widget crashed:', err);
  }

  render() {
    return this.state.failed ? this.props.fallback ?? null : this.props.children;
  }
}
