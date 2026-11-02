import { ChatWorkspace } from "@/modules/chat";

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
    <ChatWorkspace key={knowledgeSpaceId} knowledgeSpaceId={knowledgeSpaceId} />
  );
}
