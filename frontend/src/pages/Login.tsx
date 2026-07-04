import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import NavBar from "../components/NavBar";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const session = await login(email, password);
      navigate(session.role === "admin" ? "/admin" : "/studio");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Đăng nhập thất bại");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen">
      <NavBar />
      <div className="mx-auto flex max-w-md flex-col px-4 pt-20">
        <div className="card">
          <h1 className="mb-6 text-center text-2xl font-bold">Đăng nhập</h1>
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="label">Email</label>
              <input
                className="input"
                type="text"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoFocus
                required
              />
            </div>
            <div>
              <label className="label">Mật khẩu</label>
              <input
                className="input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button className="btn-primary w-full justify-center" disabled={busy}>
              {busy ? "Đang đăng nhập..." : "Đăng nhập"}
            </button>
          </form>
          <p className="mt-4 text-center text-sm text-ink-soft">
            Chưa có tài khoản?{" "}
            <Link to="/register" className="font-medium text-primary">
              Đăng ký
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
