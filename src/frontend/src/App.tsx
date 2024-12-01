// Top level component, everything runs through this
import { Outlet } from "react-router-dom";

// ? FUTURE: Find a useful MUI component to wrap a page in
export default function App() {
  return (
    <div className="body">
      <div className="content">
        <Outlet />
      </div>
    </div>
  );
}
