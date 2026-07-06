import { useIsFetching, useIsMutating } from "@tanstack/react-query";

/**
 * Thanh loading mong o dau trang, hien khi CO BAT KY thao tac nao dang chay
 * (mutation: tao/xoa/dang nhap/dang ky..., hoac lan fetch DAU TIEN cua 1
 * trang). Khong dung useIsFetching() tho de tranh nhap nhay moi lan cac
 * trang co refetchInterval (Studio/JobDetail/Admin) tu poll ngam - chi dem
 * fetch dang o trang thai "chua co du lieu lan nao" qua predicate duoi day.
 */
export default function GlobalLoadingBar() {
  const mutating = useIsMutating();
  const firstLoadFetching = useIsFetching({
    predicate: (query) => query.state.data === undefined,
  });

  if (!mutating && !firstLoadFetching) return null;

  return (
    <div className="fixed inset-x-0 top-0 z-50 h-1 overflow-hidden bg-primary-soft">
      <div className="h-full w-1/3 animate-loading-bar rounded-full bg-primary" />
    </div>
  );
}
