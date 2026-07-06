import { BrowserRouter, Route, Routes } from "react-router-dom";

import { AuthProvider, RequireAdmin, RequireAuth } from "./auth/AuthContext";
import GlobalLoadingBar from "./components/GlobalLoadingBar";
import Admin from "./pages/Admin";
import JobDetail from "./pages/JobDetail";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import NewJob from "./pages/NewJob";
import Register from "./pages/Register";
import Studio from "./pages/Studio";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <GlobalLoadingBar />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/studio"
            element={
              <RequireAuth>
                <Studio />
              </RequireAuth>
            }
          />
          <Route
            path="/studio/new"
            element={
              <RequireAuth>
                <NewJob />
              </RequireAuth>
            }
          />
          <Route
            path="/studio/jobs/:id"
            element={
              <RequireAuth>
                <JobDetail />
              </RequireAuth>
            }
          />
          <Route
            path="/admin"
            element={
              <RequireAdmin>
                <Admin />
              </RequireAdmin>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
