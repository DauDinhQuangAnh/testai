import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import NavBar from "../components/NavBar";
import Spinner from "../components/Spinner";
import { api, ApiError } from "../lib/api";
import { STATUS_LABELS } from "../lib/constants";
import type { AdminUserOut, JobOut } from "../lib/types";

export default function Admin() {
  const queryClient = useQueryClient();
  const [refreshMessage, setRefreshMessage] = useState<string | null>(null);

  const refreshCookies = useMutation({
    mutationFn: () =>
      api.post<{ cookie_count: number; path: string }>("/api/admin/refresh-cookies", {}),
    onSuccess: (result) =>
      setRefreshMessage(`Đã lấy ${result.cookie_count} cookie, lưu vào ${result.path}.`),
    onError: (err) =>
      setRefreshMessage(err instanceof ApiError ? err.message : "Làm mới cookie thất bại."),
  });

  const { data: users = [], isLoading: usersLoading } = useQuery({
    queryKey: ["admin-users"],
    queryFn: () => api.get<AdminUserOut[]>("/api/admin/users"),
  });
  const { data: jobs = [], isLoading: jobsLoading } = useQuery({
    queryKey: ["admin-jobs"],
    queryFn: () => api.get<JobOut[]>("/api/admin/jobs"),
    refetchInterval: 5000,
  });

  const deleteUser = useMutation({
    mutationFn: (id: string) => api.del(`/api/admin/users/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      queryClient.invalidateQueries({ queryKey: ["admin-jobs"] });
    },
  });

  const emailByUserId = new Map(users.map((u) => [u.id, u.email]));

  return (
    <div className="min-h-screen">
      <NavBar />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <h1 className="mb-6 text-2xl font-bold">Quản trị hệ thống</h1>

        <section className="card mb-8">
          <h2 className="mb-2 text-lg font-semibold">Cookie tải video (YouTube)</h2>
          <p className="mb-3 text-sm text-ink-soft">
            Lấy lại cookie mới từ trình duyệt đã đăng nhập sẵn (cần chạy{" "}
            <code className="rounded bg-cream px-1">
              python -m subtitle_pipeline.infrastructure.cookie_refresh --setup
            </code>{" "}
            một lần trên máy chủ trước). Dùng khi tải video báo lỗi "YouTube yêu cầu xác thực".
          </p>
          <button
            className="btn-primary"
            disabled={refreshCookies.isPending}
            onClick={() => refreshCookies.mutate()}
          >
            {refreshCookies.isPending && <Spinner />}
            {refreshCookies.isPending ? "Đang lấy cookie..." : "Làm mới cookie"}
          </button>
          {refreshMessage && <p className="mt-3 text-sm">{refreshMessage}</p>}
        </section>

        <section className="card mb-8">
          <h2 className="mb-4 text-lg font-semibold">Người dùng ({users.length})</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-line text-ink-soft">
                  <th className="py-2 pr-4">Email</th>
                  <th className="py-2 pr-4">Ngày tạo</th>
                  <th className="py-2 pr-4">Số job</th>
                  <th className="py-2"></th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-b border-line/60">
                    <td className="py-2 pr-4 font-medium">{u.email}</td>
                    <td className="py-2 pr-4 text-ink-soft">
                      {new Date(u.created_at).toLocaleDateString("vi-VN")}
                    </td>
                    <td className="py-2 pr-4">{u.job_count}</td>
                    <td className="py-2 text-right">
                      <button
                        className="btn-ghost px-3 py-1 text-xs text-red-600 hover:border-red-400"
                        disabled={deleteUser.isPending && deleteUser.variables === u.id}
                        onClick={() => {
                          if (
                            confirm(
                              `Xóa người dùng ${u.email} cùng toàn bộ ${u.job_count} job của họ?`,
                            )
                          )
                            deleteUser.mutate(u.id);
                        }}
                      >
                        {deleteUser.isPending && deleteUser.variables === u.id && (
                          <Spinner className="h-3 w-3" />
                        )}
                        Xóa
                      </button>
                    </td>
                  </tr>
                ))}
                {usersLoading && (
                  <tr>
                    <td colSpan={4} className="py-4 text-center text-ink-soft">
                      <span className="inline-flex items-center gap-2">
                        <Spinner /> Đang tải...
                      </span>
                    </td>
                  </tr>
                )}
                {!usersLoading && users.length === 0 && (
                  <tr>
                    <td colSpan={4} className="py-4 text-center text-ink-soft">
                      Chưa có người dùng đăng ký.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="card">
          <h2 className="mb-4 text-lg font-semibold">Toàn bộ job ({jobs.length})</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-line text-ink-soft">
                  <th className="py-2 pr-4">File</th>
                  <th className="py-2 pr-4">Chủ sở hữu</th>
                  <th className="py-2 pr-4">Trạng thái</th>
                  <th className="py-2 pr-4">Bước</th>
                  <th className="py-2">Tạo lúc</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((j) => (
                  <tr key={j.id} className="border-b border-line/60">
                    <td className="max-w-xs truncate py-2 pr-4 font-medium" title={j.filename}>
                      <Link to={`/studio/jobs/${j.id}`} className="hover:text-primary">
                        {j.filename}
                      </Link>
                    </td>
                    <td className="py-2 pr-4 text-ink-soft">
                      {j.user_id ? (emailByUserId.get(j.user_id) ?? j.user_id.slice(0, 8)) : "—"}
                    </td>
                    <td className="py-2 pr-4">{STATUS_LABELS[j.status] ?? j.status}</td>
                    <td className="py-2 pr-4 text-ink-soft">{j.stage_label}</td>
                    <td className="py-2 text-ink-soft">
                      {new Date(j.created_at).toLocaleString("vi-VN")}
                    </td>
                  </tr>
                ))}
                {jobsLoading && (
                  <tr>
                    <td colSpan={5} className="py-4 text-center text-ink-soft">
                      <span className="inline-flex items-center gap-2">
                        <Spinner /> Đang tải...
                      </span>
                    </td>
                  </tr>
                )}
                {!jobsLoading && jobs.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-4 text-center text-ink-soft">
                      Chưa có job nào.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}
