import { Request } from 'express';

export interface OrgContext {
  orgId: string;
  userId?: string;
  apiKeyId?: string;
}

export const getOrgContext = (req: Request): OrgContext => {
  if (!req.auth?.orgId) {
    throw Object.assign(new Error('Organization context missing'), { status: 401 });
  }

  return {
    orgId: req.auth.orgId,
    userId: req.auth.user?.id,
    apiKeyId: req.auth.apiKey?.id,
  };
};
