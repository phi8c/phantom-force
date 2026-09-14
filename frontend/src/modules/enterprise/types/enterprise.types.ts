export type EnterpriseStatus = "ACTIVE" | "INACTIVE";

export type Enterprise = {
  id: string;
  code: string;
  name: string;
  description: string | null;
  status: EnterpriseStatus | string;
  created_at: string | null;
  updated_at: string | null;
};

export type CreateEnterprisePayload = {
  code: string;
  name: string;
  description?: string | null;
  status?: EnterpriseStatus;
};

export type UpdateEnterprisePayload = Partial<CreateEnterprisePayload>;

export type EnterpriseListResponse = {
  items: Enterprise[];
  next_cursor: string | null;
  has_more: boolean;
};

export type EnterpriseOption = {
  id: string;
  code: string;
  name: string;
};
