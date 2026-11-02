"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowUpRight, Sparkles } from "lucide-react";
import { AuthLoadingState, isManagementSession, isUnauthorizedAuthError, useCurrentUser } from "@/modules/auth";
import { useKnowledgeSpaceList } from "@/modules/knowledge-space";
import { Button } from "@/components/ui/button";

function SpacePicker() {
  const [page, setPage] = useState(1);
  const spaces = useKnowledgeSpaceList({ page, page_size: 20, status: "ACTIVE" });
  return <div className="mx-auto max-w-4xl px-6 py-12"><Link href="/admin" className="text-sm text-muted-foreground">← Quay lại Admin</Link><Sparkles className="mb-5 mt-14 size-9 text-primary" /><h1 className="text-3xl font-semibold tracking-tight">Trò chuyện với tri thức của bạn</h1><p className="mb-8 mt-3 text-muted-foreground">Chọn knowledge space để bắt đầu. Bạn đang dùng phiên đăng nhập admin.</p>
    {spaces.isLoading && <p role="status">Đang tải knowledge spaces…</p>}
    {spaces.isError && <div role="alert">Không tải được knowledge spaces. <Button variant="outline" onClick={() => void spaces.refetch()}>Thử lại</Button></div>}
    {spaces.data?.items.length === 0 && <p>Chưa có knowledge space đang hoạt động. Hãy tạo và cấu hình trong Admin.</p>}
    <div className="grid gap-4 sm:grid-cols-2">{spaces.data?.items.map((space) => <Link key={space.id} href={`/chat/${space.id}`} className="group rounded-2xl border p-6 transition-colors hover:bg-muted/50"><div className="flex justify-between gap-3"><h2 className="font-semibold">{space.name}</h2><ArrowUpRight className="size-4 text-muted-foreground" /></div><p className="mt-2 text-xs text-muted-foreground">{space.enterprise_name} · {space.code}</p><p className="mt-4 line-clamp-2 text-sm text-muted-foreground">{space.description || "Khám phá dữ liệu và đặt câu hỏi trong knowledge space này."}</p></Link>)}</div>
    {spaces.data && spaces.data.total > 20 && <div className="mt-6 flex items-center justify-between"><Button variant="outline" disabled={page === 1 || spaces.isFetching} onClick={() => setPage(page - 1)}>Trang trước</Button><span className="text-sm">Trang {page}</span><Button variant="outline" disabled={page * 20 >= spaces.data.total || spaces.isFetching} onClick={() => setPage(page + 1)}>Trang sau</Button></div>}
  </div>;
}

export function ChatEntryPage() {
  const session = useCurrentUser();
  const router = useRouter();
  const management = isManagementSession(session.data);
  useEffect(() => {
    if (session.isLoading) return;
    if (isUnauthorizedAuthError(session.error)) router.replace("/admin/login");
    else if (session.data && !management) router.replace(session.data.knowledge_space_id ? `/chat/${session.data.knowledge_space_id}` : "/admin/login");
  }, [session.data, session.error, session.isLoading, management, router]);
  if (session.isError && !isUnauthorizedAuthError(session.error)) return <div role="alert" className="p-8">Không thể kiểm tra phiên đăng nhập. <Button onClick={() => void session.refetch()}>Thử lại</Button></div>;
  return management ? <SpacePicker /> : <AuthLoadingState />;
}
