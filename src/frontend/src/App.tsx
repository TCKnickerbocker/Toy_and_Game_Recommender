import React from 'react';
import { Link, Outlet } from 'react-router-dom';

export default function App() {
  return (
    <div className="body">
      <div className="content">
        <Outlet />
      </div>
    </div>
  );
}
