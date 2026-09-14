import { IngestionPage } from "@/modules/ingestion";

interface IngestionPageRouteProps {
  params: Promise<{
    knowledgeSpaceId: string;
  }>;
}

export default async function Page({
  params,
}: IngestionPageRouteProps) {
  const { knowledgeSpaceId } = await params;

  return (
    <IngestionPage
      knowledgeSpaceId={knowledgeSpaceId}
    />
  );
}