import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

export default function NavBar() {
  const { isLoggedIn, isAdmin, email, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-20 border-b border-line bg-cream/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link to="/" className="flex items-center gap-2 text-lg font-bold">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-white">
            V
          </span>
          VietDub<span className="text-primary">Studio</span>
        </Link>
        <nav className="flex items-center gap-3">
          {isLoggedIn ? (
            <>
              <Link to="/studio" className="btn-ghost">
                Studio
              </Link>
              {isAdmin && (
                <Link to="/admin" className="btn-ghost">
                  Quản trị
                </Link>
              )}
              <span className="hidden text-sm text-ink-soft sm:block">{email}</span>
              <button
                className="btn-ghost"
                onClick={() => {
                  logout();
                  navigate("/");
                }}
              >
                Đăng xuất
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn-ghost">
                Đăng nhập
              </Link>
              <Link to="/register" className="btn-primary">
                Dùng thử miễn phí
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
