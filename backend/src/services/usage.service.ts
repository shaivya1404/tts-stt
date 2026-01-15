import { Prisma, UsageType } from '@prisma/client';

import prisma from '../lib/prisma';

export interface UsageRecordInput {
  orgId: string;
  apiKeyId?: string;
  type: UsageType;
  units: number;
  metadata?: Prisma.InputJsonValue;
}

export const UsageService = {
  async recordUsage(input: UsageRecordInput) {
    return prisma.usageRecord.create({
      data: {
        orgId: input.orgId,
        apiKeyId: input.apiKeyId,
        type: input.type,
        units: input.units,
        metadata: input.metadata,
      },
    });
  },
};
