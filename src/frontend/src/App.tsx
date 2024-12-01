// Top level component, everything runs through this
import { Outlet } from "react-router-dom";

export default function App() {
  return (
    <div className="body">
      <div className="content">
        <Outlet />
      </div>
    </div>
  );
}
