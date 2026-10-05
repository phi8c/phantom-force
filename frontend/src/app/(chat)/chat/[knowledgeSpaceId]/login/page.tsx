import { KnowledgeSpaceLoginView } from "@/modules/auth";

interface KnowledgeSpaceLoginPageProps {
  params: Promise<{
    knowledgeSpaceId: string;
  }>;
}

export default async function KnowledgeSpaceLoginPage({
  params,
}: KnowledgeSpaceLoginPageProps) {
  const { knowledgeSpaceId } = await params;
  return <KnowledgeSpaceLoginView knowledgeSpaceId={knowledgeSpaceId} />;
}
