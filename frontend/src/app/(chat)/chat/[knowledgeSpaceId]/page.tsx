import { KnowledgeSpaceSessionHeader } from "@/modules/auth";

interface KnowledgeSpaceChatPageProps {
  params: Promise<{
    knowledgeSpaceId: string;
  }>;
}

export default async function KnowledgeSpaceChatPage({
  params,
}: KnowledgeSpaceChatPageProps) {
  const { knowledgeSpaceId } = await params;

  return (
    <div className="min-h-screen bg-background">
      <KnowledgeSpaceSessionHeader knowledgeSpaceId={knowledgeSpaceId} />
      <main className="p-6">Chat</main>
    </div>
  );
}
