interface KnowledgeSpacePageProps {
  params: Promise<{
    knowledgeSpaceId: string;
  }>;
}

export default async function Page({
  params,
}: KnowledgeSpacePageProps) {
  const { knowledgeSpaceId } = await params;

  return (
    <div className="space-y-6 p-6">
      <div>
        <p className="text-sm text-muted-foreground">
          Knowledge Space
        </p>

        <h1 className="mt-1 text-2xl font-semibold tracking-tight">
          Knowledge Space Dashboard
        </h1>

        <p className="mt-2 text-sm text-muted-foreground">
          Manage sources, documents, ingestion, workers,
          models, and knowledge processing.
        </p>
      </div>

      <div className="rounded-xl border bg-card p-5">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Knowledge Space ID
        </p>

        <p className="mt-2 font-mono text-sm">
          {knowledgeSpaceId}
        </p>
      </div>
    </div>
  );
}